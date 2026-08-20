<!-- progress/review_F-007.md -->
# F-007 · Front de carga y revisión — Informe de review

- **Feature:** F-007 · Front de carga y revisión
- **Rama:** `feature/F-007-front`
- **Nivel de rigor:** `estandar` (declarado en `harness/features.json`)
- **Fecha:** 2026-08-20

## Veredicto

# APROBADO

*(Segunda pasada, 2026-08-20. Los tres cambios requeridos en la primera están
resueltos y **verificados por el reviewer**, no dados por buenos: ver la
sección **17 · Cierre**. El veredicto original y su razonamiento se conservan
abajo, tachados en su encabezado pero intactos en el cuerpo, porque explican
qué se pidió y por qué.)*

## ~~Veredicto de la primera pasada: CHANGES_REQUESTED~~ (resuelto)

**El front funciona.** T14 se ejecutó durante esta review y el humano lo firmó
con un «funciona a la perfección». La implementación es de las más sólidas del
repositorio y no se pide rehacer **ni una línea de código**. Lo que falta es
acabado del registro, en tres puntos concretos:

1. **C5 · T14 marcada `[x]` con su tabla de ocho puntos entera en
   `PENDIENTE`** (`progress/impl_F-007.md:950-959`). «Funciona a la
   perfección» es el veredicto de quien **usa** la pantalla; los puntos **3**
   (nunca más de 6 peticiones en vuelo: *la* comprobación visual del criterio
   de aceptación 3), **6** (revalidar no gasta IA) y **8** (**ningún DNI en la
   consola**, R28) no se ven usando el front, se ven en **DevTools**. Hay que
   anotar qué se miró de verdad.
2. **C4 · trazabilidad** — **R5, R6, R19 y R22** no tienen ningún test, y la
   tabla de trazabilidad de `requirements.md` afirma que sí. El que importa es
   **R19**: la confirmación explícita antes de archivar.
3. **C2 · coherencia del estado** — `progress/current.md` se contradice a sí
   mismo: la cabecera dice que F-007 está implementada y, más abajo, secciones
   heredadas de la sesión anterior dicen que F-006 está `in_progress` y
   **RECHAZADA** y que F-007 está `pending`. Una sesión que siga el paso 2 del
   protocolo de `CLAUDE.md` se iría a rehacer una feature cerrada.

Los tres son de minutos. **Ninguno toca código de producción.**

**Lo que NO motiva el rechazo:** ni los 3 supervivientes de mutación (en
`estandar` están bien como están), ni la ausencia de `comando_tests` (es
deliberada y verifiqué que el front **sí** se comprueba), ni las tres
observaciones de diseño de T14 (ya son **F-020**).

**Aviso operativo, aparte del veredicto:** durante la review dejé
—sin querer— un `__pycache__` envenenado que rompía la suite del front de
forma invisible. **Ya está limpio y reverificado**, pero el fallo del arnés que
lo causó sigue ahí: **sección 16** y propuesta **P4**.

## Qué exige el nivel `estandar`

Según `harness/rigor.json` y `CHECKPOINTS.md`:

| Puerta | ¿Exigida en `estandar`? |
|---|---|
| Tests trazables requisito → test | Sí |
| Fase RED | Sí, **solo en los requisitos centrales** |
| Cobertura de líneas cambiadas ≥ 80 % | Sí |
| Campaña de mutación con supervivientes **analizados** | Sí |
| **Cero** supervivientes | **NO** (eso es `critico`) |
| Fase RED en **todo** | **NO** (eso es `critico`) |

Se revisa contra esa vara, no contra la de `critico`.

---

## 1 · Portero y suites (verificación propia)

`bash harness/init.sh` ejecutado tal cual por el reviewer:

```
[OK] Arnés v1.5.2 (2026-08-18)
     19 features, 13 abiertas, en curso: ['F-007'], bloqueadas: ninguna
[OK] pytest en verde (con medición de cobertura)   16 passed
     2 servicio(s): api (python), front (python)
[OK] harness/servicios.json válido
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: 98.3% de 116 líneas cambiadas cubiertas
     (114/116, umbral 80%, nivel estandar)
[OK] Rama actual: feature/F-007-front
ENTORNO LISTO. Puedes trabajar.
```

Los dos `[OK]` de servicio salieron **de caché** («árbol sin cambios desde el
último verde»), así que **se relanzaron las dos suites a mano**, sin caché:

| Suite | Comando del reviewer | Resultado |
|---|---|---|
| `front` | `python -m pytest -q` en `services/postventa-front` | **74 passed en 1,45 s** |
| `api` | `.venv\Scripts\python.exe -m pytest -q` en `services/postventa-api` | **924 passed, 10 skipped en 23,94 s** |
| JS | `node --test "tests_js/*.test.js"` (Node v24.14.1) | **84 pass, 0 fail, 0 skipped, 314 ms** |

Árbol de git **limpio** (`git status --porcelain` sin salida); `.coverage` y
`coverage.json` del front están cubiertos por `.gitignore` (líneas 22 y 24).

---

## 2 · El agujero que la feature venía a cerrar: ¿se comprueba el front?

**Sí, y se ha verificado empíricamente.** `[x]`

`harness/servicios.json` declara **dos** servicios, `api` y `front`. El front
va **sin `comando_tests` a propósito** y con `lenguaje: "python"`; el `$doc`
del fichero razona por qué, y `tests/test_f007_declaracion.py` lo vigila con
tests. La cadena efectiva es:

```
init.sh → pytest en services/postventa-front
        → tests/test_f007_js.py → node --test "tests_js/*.test.js"
```

Es decir: **sí ejecuta algo de verdad** (84 tests de JavaScript), aunque el
campo `comando_tests` no exista. La ausencia del campo no es un olvido: con
`lenguaje: "python"` el arnés lanza `pytest` en la carpeta del servicio, y
declarar `lenguaje: "otro"` + `comando_tests` habría dejado `dev_server.py`
como **NO MEDIDO** en la puerta de cobertura, que es justo el problema que
expulsó al front de F-001.

### El `skip` silencioso: comprobado que no existe

Prueba del reviewer — ejecutar la suite del front **con `node` fuera del
`PATH`**:

```
PATH="/usr/bin:/bin" .venv/Scripts/python.exe -m pytest tests/test_f007_js.py -q

FAILED tests/test_f007_js.py::test_f007_r32_node_esta_disponible
    AssertionError: sin node no se puede ejecutar la suite de JavaScript
FAILED tests/test_f007_js.py::test_f007_r32_la_suite_de_javascript_esta_en_verde
FAILED tests/test_f007_js.py::test_f007_r32_todos_los_modulos_del_front_compilan
3 failed, 1 passed in 0.10s
```

**Falla en rojo, no se salta.** No hay `pytest.skip`, ni `skipif`, ni
`importorskip` en el fichero: es un `assert` con mensaje explícito. R32
cumplido y verificado de forma independiente.

Además, `test_f007_r32_hay_tests_de_javascript_que_ejecutar` cierra el hueco
complementario: una carpeta `tests_js/` vacía haría que `node --test` saliera
en verde sin probar nada, y ese test lo impide.

---

## 3 · D4 · La remesa no se persiste: ¿guarda algo el navegador?

**No guarda nada. Verificado con barrido propio.** `[x]`

Barrido del reviewer sobre `js/*.js`, `index.html` y los `.py` del front
(`localStorage|sessionStorage|indexedDB|document.cookie|window.name|caches.`),
**sin** filtrar comentarios, para no depender del helper del implementer:

```
js/traza.js:6:  // ... ni consola, ni localStorage, ni sessionStorage, ni URL.   (comentario)
tests/test_f007_documentacion.py:70   (aserción sobre el README)
tests/test_f007_estaticos.py:317,324  (la guardia)
```

**Ni una sola aparición en código ejecutable.** Las cuatro coincidencias son
un comentario y la propia guardia que lo prohíbe.

La guardia es `test_f007_r30_el_front_no_guarda_nada_en_el_navegador`
(`tests/test_f007_estaticos.py:317`), que además quita comentarios antes de
mirar para no confundir «nombrar la prohibición» con «usarla». D4 respetado:
la persistencia se aplaza a F-019 (endpoints en `postventa-api`), y queda
escrito, no olvidado.

## 4 · Datos personales (R28–R30) — barrido propio

`[x]`

**Consola.** Único `console.*` de todo el front: `js/traza.js:68-69`
(`console.info`), y llega **después** del filtro. `traza.js` recorta a cuatro
claves (`hash`, `paso`, `estado`, `http`) **y solo si son primitivas** —un
objeto anidado bajo una clave permitida también se descarta, para que un
`{valor: "..."}` no se cuele—. El resto de módulos no toca `console`, y
`test_f007_r36_app_js_es_solo_pegamento` prohíbe `console.` dentro de
`app.js`. Registro por un solo sitio, y ese sitio vigilado.

**DNI y base64 en el árbol.** Barrido propio con
`\b[0-9]{8}[A-HJ-NP-TV-Z]\b` sobre **todos** los ficheros del diff
(`git diff --name-only dev...HEAD`): 16 coincidencias, **todas** con los ocho
dígitos iguales (`00000000T`, `11111111H`), es decir, la convención de
inventado. Ni un patrón sospechoso. Ningún `.pdf`, `.zip` ni imagen bajo
`services/postventa-front/`.

`tests/test_f007_sin_datos_reales.py` automatiza los tres barridos
(binarios, DNI, blobs de base64 ≥ 120 caracteres) y — mérito — incluye un
**meta-test** (`..._la_guardia_del_dni_distingue_inventado_de_sospechoso`)
que compone un DNI sospechoso en trozos para demostrar que el barrido mira
de verdad. Es exactamente la defensa contra el barrido vacío.

**URL.** No se ha encontrado ningún `history.pushState`, `location.search` ni
construcción de query con valores de campo.

## 5 · Identificadores, secretos y llamadas reales (punto 7)

`[x]`

- **GUID de tenant o suscripción en el diff:** ninguno.
- **IPs privadas (10/8, 192.168/16, 172.16/12):** ninguna.
- **Secretos:** las únicas coincidencias del barrido son
  `staticwebapp.config.json` → `"clientSecretSettingName": "AZURE_CLIENT_SECRET"`,
  que es el **nombre del App Setting**, no el secreto, y
  `tests/test_f007_dev_front_ps1.py:55`, que **prohíbe** `password`, `secret`,
  `TENANT` y `C:\Users\` dentro del script de arranque.
- **`<TENANT_ID>` intacto** en `staticwebapp.config.json`, con su `$comentario`
  explicando que se resuelve en el despliegue (F-010). Vigilado por
  `test_f007_estaticos.py`.
- **Red real desde los tests:** ninguna. En JavaScript el `fetch` es **siempre
  un doble inyectado** (`tests_js/api.test.js`), y no hay ni una URL absoluta
  a ningún host en `tests_js/`. En Python, `tests/conftest.py` monta una
  **guardia de sockets de sesión** que sustituye `socket.socket.connect`
  durante toda la ejecución, y `test_f007_dev_server.py` proxia con un doble
  de `http.client.HTTPConnection` inyectado por `monkeypatch`. Ni un socket
  hacia la Function ni hacia SharePoint.

## 6 · D2 · El límite de concurrencia: 3 partes, 6 peticiones vivas

**Implementado y probado de verdad, no declarado.** `[x]`

La cadena completa, verificada fichero a fichero:

| Eslabón | Dónde | Qué hace |
|---|---|---|
| Constante | `js/config.js` → `CONCURRENCIA_PARTES: 3` | Un solo sitio, con el porqué escrito (6 conexiones por origen en HTTP/1.1; un solo worker de `func start`) |
| Limitador | `js/cola.js` → `ejecutarConLimite(tareas, limite, alTerminar)` | Plazas, no lotes. Las tareas se **invocan dentro**, no antes: invocarlas fuera ya habría disparado las peticiones |
| Cableado | `js/app.js:151-155` → `window.Cola.ejecutarConLimite(partes.map(...), config.CONCURRENCIA_PARTES, ...)` | Una tarea de la cola = **un parte entero** |
| 1 parte = 2 peticiones | `js/pipeline.js::procesarParte` → `Promise.all([api.extraer, api.firma])`, y `api.validar` **después** | 3 partes × 2 = **6 peticiones vivas**, como pide D2 |

Detalle que merece nota: un `limite` no entero o `< 1` **lanza**, no degrada a
«sin límite». Degradar en silencio sería exactamente lo que el criterio de
aceptación 3 prohíbe, y sin que nadie se entere.

`reintentarParte` (R11) no abre un camino aparte: vuelve a llamar a
`_porLaCola`, así que el reintento respeta el mismo límite.

### Los tests observan la concurrencia, no la asumen

`tests_js/cola.test.js` (13 tests) usa promesas diferidas controladas a mano
—**sin relojes ni `setTimeout` reales**, un acierto: un test de concurrencia
que dependa de tiempos falla en la máquina de otro— y un contador de tareas
vivas con su máximo observado. Lo relevante:

- `f007 R7: nunca hay más tareas vivas que el límite` — **22 tareas** (la
  remesa real de Mirasierra) con límite 3; comprueba `vivas == 3` al arrancar
  y `maximo <= 3` **después de cada una** de las 22 resoluciones, y al final
  `maximo == 3` exacto.
- `no arranca la siguiente hasta que una plaza queda libre` — dos `respirar()`
  seguidos sin resolver nada y sigue habiendo 2 vivas.
- `un límite menor que 1 es un error, no un «sin límite» silencioso` — 0, −1 y
  1.5 rechazan.
- `una tarea que falla libera su plaza` (R12), `un error no para a los demás`
  (R10), `los resultados salen en el orden de entrada` y `la cola no llama a
  una tarea más de una vez`.

Es prueba real del criterio de aceptación 3 en la unidad. La comprobación
**visual** de las 6 peticiones en DevTools es T14, la tarea manual del humano
(ver sección 10).

## 7 · D3 · Campo corregido a mano → confianza 100 y marca de editado

**Las dos mitades están, y la marca sí distingue.** `[x]`

`js/pipeline.js::aplicarEdiciones` escribe, para un campo corregido:

```js
campos[nombre] = { valor: normalizarValor(correcciones[nombre]),
                   confianza_pct: 100,
                   editado: true };
```

y para un campo **no** tocado, `{valor, confianza_pct}` **sin** la clave
`editado`. La distinción «lo escribió una persona» / «lo dijo la IA» es por
tanto la presencia de la clave, no un valor de confianza ambiguo: dos campos
al 100 % se siguen distinguiendo si uno viene del modelo.

Además `aplicarEdiciones` **no muta** la extracción original
(`Object.assign({}, extraccion, ...)`), así que la respuesta íntegra de
`/api/extraer` se conserva y se puede volver a ella.

En pantalla: `index.html:199-200` pinta la etiqueta `editado` con
`x-show="estaEditado(nombre)"`, en verde, junto al porcentaje de confianza.

Probado en `tests_js/pipeline.test.js`:

- `f007 R16: el campo corregido queda MARCADO como editado (D3)` — afirma
  `editado === true` **y** `confianza_pct === 100`, **y** que un campo que
  nadie tocó `notEqual(..., true)`. Las dos mitades y el contraste.
- `f007 R16: corregir un campo no toca el resto del cuerpo ni la traza` —
  `deepEqual` sobre la `traza` y comprobación de que el original no se muta.
- `f007 R15: un campo corregido a mano deja de ser dudoso` — cierra el bucle
  con R15: por eso el semáforo puede pasar a verde.

## 8 · R29 · Qué viaja a `/api/archivar`

`[x]` `cuerpoDeArchivo` compone **exactamente** el fichero y cinco campos
(`hash`, `codigo_obra`, `numero_incidencia`, `veredicto`, `destino`). Y no es
solo el botón: la función **se niega** a componer nada cuyo veredicto no sea
`apto` + `archivo_y_cierre` (R21) y nada ya archivado —la defensa contra el
doble clic está en la lógica, no en el `:disabled`—.

El test `f007 R29: al archivar NO viajan ni el DNI ni las observaciones` no se
conforma con mirar las claves: **concatena todos los valores del `FormData` y
comprueba que no contienen el DNI ni las observaciones inventadas**. Es la
comprobación correcta, porque el dato podría colarse dentro de otro campo.

## 9 · `dev_server.py` se prueba de verdad (D1)

`[x]` No es un test de humo. `tests/test_f007_dev_server.py` son **30 tests de
comportamiento** (25 funciones, una parametrizada), con dobles de `http.client.HTTPConnection` inyectados por
`monkeypatch`: enrutado `/api/*` contra fichero estático, `do_POST` sobre ruta
estática → **405**, `OPTIONS` → 204 con CORS, `host`/`connection` **no** se
reenvían mientras `content-type`/`accept` sí, `DEV_FAKE_PRINCIPAL` solo viaja
si está declarado, `Content-Length` no numérico no bloquea leyendo del socket,
cabeceras de salto suprimidas, destino `https` usa la conexión segura, backend
inalcanzable → **502 en JSON** (con `Content-Type` y `Content-Length`
afirmados), CLI (`--port`, `--api`, `--root`), `Ctrl+C` → 0, sin `index.html`
→ **código 1**, hilos demonio, `allow_reuse_address`, y los 300 s de timeout
al backend.

**Cobertura medida por el reviewer**, no leída del informe:

```
python -m coverage run --source=. -m pytest -q ; python -m coverage report --include="dev_server.py" -m

Name            Stmts   Miss  Cover   Missing
dev_server.py     116      2    98%   52, 188
```

Coincide con la puerta (114/116, 98,3 %). Las dos líneas sin cubrir son
`DevHandler.__init__` (línea 52, `super().__init__(...)`, exige un socket
aceptado) y `sys.exit(main())` (línea 188, bajo `if __name__ == "__main__"`).
**Inalcanzables sin levantar un servidor real, que es justo lo que R33
prohíbe.** Justificación correcta y verificada.

## 10 · R33 · La guardia de red muerde (sonda del reviewer)

`[x]` La guardia de `tests/conftest.py` no tiene test propio, así que la
comprobé con una **sonda temporal**, ejecutada y borrada acto seguido:

```python
def test_sonda(): socket.socket().connect(("127.0.0.1", 9))
```

```
E  RuntimeError: la suite del front no puede abrir conexiones de red: un test
   ha intentado conectar a ('127.0.0.1', 9). Usa un doble de
   http.client.HTTPConnection.
tests\conftest.py:50: RuntimeError
1 failed in 0.08s
```

La guardia **está activa y bloquea de verdad**. `git status` limpio después.

*(Nota menor: el docstring de la fixture dice que se hace a mano «porque
`monkeypatch` es de alcance función y esto tiene que estar puesto también
durante la recogida de tests». Una fixture de sesión tampoco corre durante la
recogida; el motivo real —y suficiente— es el alcance. Es una imprecisión del
comentario, no del código.)*

## 11 · Mutación (C4 bis) — verificada de forma independiente

`[x]` **Nivel `estandar`: la campaña se exige, los cero supervivientes no.**

El informe declara **«Tiempo total 12,1 s»**, por debajo del umbral de 5
minutos de `CHECKPOINTS.md`, así que **reejecuté la campaña entera**, no solo
el recálculo puro:

```
python -m harness.mutacion --feature F-007 --workers 1 --salida <scratchpad>/mutacion_F-007_reviewer.md

20 mutantes evaluados, 17 muertos, 3 supervivientes, 0 timeouts en 28.8 s
```

| Métrica | Informe del implementer | Reejecución del reviewer |
|---|---|---|
| Alcance | `dev_server.py`, 188 líneas | **idéntico** |
| Mutantes | 20 | **20** |
| Muertos | 17 | **17** |
| Supervivientes | 3 | **3** |
| Timeouts | 0 | **0** |

**Coinciden exactamente.** Salida escrita en el scratchpad, **nunca** en
`progress/`; `git status` limpio después.

*(Apunte de operativa: la campaña paralela se niega a correr con el árbol
sucio —mi propio `review_F-007.md` sin trackear bastaba—, y hubo que usar
`--workers 1`. La herramienta lo dice con un mensaje claro; no es un
problema, pero conviene saberlo para la próxima review.)*

### Los tres supervivientes: análisis verificado

Los tres son, verificado en `dev_server.py:169`, `:171` y `:175`, **la misma
línea**: `log.info("=" * 60)`, mutada a `"=" * 61` por el operador `entero`.
Son los separadores del rótulo que `main()` imprime al arrancar. El análisis
—«mutante equivalente: cambia cuántos `=` ve el humano en su terminal, no el
comportamiento del proxy, ni el código de salida, ni una respuesta HTTP»— **se
sostiene**. Fijarlo con un test de longitud del rótulo compraría un mutante
muerto a cambio de un test que se rompe sin que se rompa nada.

Nota de solidez: el **mismo** rótulo tiene un segundo mutante por operador
`aritmetico` (`"=" * 60` → `"=" // 60`), y ese sí **muere** en las tres
líneas. Es decir, el rótulo no está sin ejecutar: se ejecuta y se rompe si
deja de ser válido; lo único que nadie afirma es su anchura. Refuerza la tesis
del mutante equivalente.

### Sobre el commit `08820cc`

El mensaje —«análisis idéntico en los tres supervivientes, **para que
sobreviva al reviewer**»— suena a maquillaje, así que lo miré a fondo. **No lo
es.** `harness/mutacion.py:497-541` (`analisis_escritos`) indexa los análisis
por `clave_de_mutante(fichero, operador, original, mutado)` —**sin el número de
línea**— y su propio docstring dice: *«Si dos supervivientes comparten clave
con análisis distintos, la clave se descarta entera»*. Como los tres
supervivientes comparten clave, tener tres textos distintos habría hecho que
`harness.mutacion` **borrara el análisis** al reejecutar la campaña, dejando
tres secciones en `PENDIENTE` delante del reviewer.

«Para que sobreviva al reviewer» significa, literalmente, *«para que el
análisis no se pierda cuando el reviewer reejecute la campaña»*. Es
comportamiento correcto de la herramienta, y el propio informe lo explica en
el cuerpo del análisis. **Ninguna manipulación.** El pie de página *«Análisis
traído de la campaña anterior»* que llevan los tres es la prueba de que el
mecanismo funcionó en mi reejecución.

## 12 · Trazabilidad requisito → test

Barrido automático de los nombres de test (`test_f007_rN_*` en Python,
`f007 RN:` en node) contra los 37 requisitos EARS:

| | Requisitos |
|---|---|
| **Con test trazable (31)** | R1, R2, R3, R4, R7–R18, R20, R21, R23–R32, R34, R35, R36 |
| **SIN test trazable (6)** | **R5, R6, R19, R22**, R33, R37 |

Detalle de los seis:

| Req | Qué pide | Situación real |
|---|---|---|
| **R5** | Tras un 200 de `/api/split`, mostrar `total_partes`, `avisos` y una fila por parte | **Implementado** (`index.html:109-112`, `app.js`), **sin test**. La parte de cliente sí (`f007 R4: trocear envía el multipart de la remesa tal cual`), la de presentación no |
| **R6** | Tras un 400, mostrar `error` y `avisos` y volver al estado inicial sin filas a medias | **Parcial**: `api.test.js:162-169` prueba que `error` y `avisos` se propagan; «volver al estado inicial» (`app.js:113`, `reiniciar()`) **sin test** |
| **R19** | Botón de archivar con **confirmación explícita antes de la primera petición** | **Implementado** (`app.js:281-286`, `confirmandoArchivo` en dos pasos), **sin test y sin punto explícito en T14** |
| **R22** | Mostrar `nombre_fichero`, `carpeta`, `estado` y el enlace a `web_url` | **Implementado** (`index.html:264`), **sin test** |
| **R33** | La suite no abre red real | **Cumplido y verificado por el reviewer** (sección 10). Falta el test que afirme que la guardia muerde |
| **R37** | `init.sh` en verde | **Cumplido** (exit 0). Es el portero mismo; no cabe un test que se pruebe a sí mismo. **N/A justificado** |

R33 y R37 los doy por buenos: uno lo verifiqué a mano, el otro es el propio
portero. **R5, R6, R19 y R22 no.** Los cuatro viven en `index.html` + `app.js`,
que `design.md` deja fuera de los tests a propósito («`app.js` es pegamento»),
decisión razonable y bien defendida con dos guardias estáticas. **El problema
no es la decisión: es que la tabla de trazabilidad de `requirements.md` dice
que esos cuatro los cubren `pipeline.test.js` y `seleccion.test.js`, y no es
cierto.** Para R36 la tabla sí dice «MANUAL (humano), T14»; para estos cuatro,
no.

Y de los cuatro, **R19 es el que importa**: es la confirmación explícita que
separa un clic de una tanda de subidas a SharePoint. Hoy no la comprueba ni un
test ni ninguno de los ocho puntos de T14.

## 13 · Convenciones y reglas duras (C3)

| Comprobación | Resultado |
|---|---|
| Primera línea de cada fichero con su ruta relativa | `[x]` los **25** ficheros nuevos la llevan, con el comentario propio de cada lenguaje (`//`, `#`, `/* */`, `<!-- -->`) |
| Sin `print()` de debug | `[x]` ninguno; el único registro es `traza.js` y el `logging` de `dev_server.py` |
| Sin secretos hardcodeados | `[x]` verificado en la sección 5 |
| Sin dependencias nuevas | `[x]` `dev_server.py` es biblioteca estándar; `node --test` viene con Node; ni `package.json` ni `node_modules` |
| Ningún cambio en `services/postventa-api/` | `[x]` el diff no toca **ni un fichero** del backend |
| La unidad de trabajo es el **parte**, no el fichero | `[x]` explícito en el vocabulario de la spec y en el código: tras `/api/split` todo se razona por parte |
| Nada se archiva sin haber pasado las validaciones | `[x]` `cuerpoDeArchivo` **lanza** si el veredicto no es `apto` + `archivo_y_cierre` |
| Nada se sube a SharePoint desde local | `[x]` la puerta de entorno de F-006 responde 503 y el front lo pinta como estado de entorno, no como fallo (R25) |
| Ningún PDF con datos personales en git | `[x]` `git diff --name-only dev...HEAD`: ni un binario; `test_f007_r30_...` lo vigila en adelante |
| `ruff` | `[x]` 56 avisos, **los mismos** de deuda previa; F-007 no añade ninguno |
| Todo en español | `[x]` código, comentarios, tests y commits |
| Arquitectura hexagonal | **N/A justificado**: el front no es hexagonal. Su equivalente —la lógica en módulos puros y probados, el pegamento aparte— está respetado y **vigilado por dos tests** (`app.js` no puede contener `fetch(`, `new FormData`, `setTimeout`, `JSON.stringify`, `console.` ni `archivo_y_cierre`) |

## 14 · Estado de la sesión (C5) — un defecto

**`tasks.md`:** 15 de 16 `[x]`; la abierta es **T14**, `MANUAL (humano)`.

**Commits:** uno o más por tarea, todos con formato `F-007 Tn: ...` (T1 a T16).
Correcto.

**Árbol:** limpio. `.coverage` y `coverage.json` del front están en
`.gitignore`. Sin artefactos sospechosos versionados.

**`features.json`:** F-007 `in_progress`, coherente con no estar cerrada.
`history.md` tiene el resumen de las seis features `done`, F-006 incluida.

**`progress/current.md` se contradice a sí mismo.** El bloque de cabecera está
al día (F-007 implementada, 2026-08-20), pero más abajo sobreviven secciones de
la sesión anterior que afirman lo contrario:

| Línea | Lo que dice `current.md` | La realidad (`features.json`, 19 features) |
|---|---|---|
| `## Estado del backlog: **18** features` | 18 | **19** |
| «**`in_progress`**: **F-006**… Implementada, **RECHAZADA en la primera review**» | F-006 en curso y rechazada | F-006 está **`done`** y cerrada en `history.md` |
| «**`pending`**: F-007 a F-018» | F-007 pendiente | F-007 **`in_progress`** |
| `## Lo siguiente: F-006, y lo que hay que saber de Graph` — «Solo falta la PARADA 1» | F-006 es la siguiente | F-006 terminó |
| «Mientras el merge no esté hecho, F-006 no debe arrancar en paralelo» | — | El merge se hizo |

**Por qué no es cosmético.** El protocolo de `CLAUDE.md` ordena, en su paso 2:
«Lee `progress/current.md`. Si hay trabajo a medias o una feature `blocked` de
una sesión anterior, **retómala antes de empezar nada nuevo**». Una sesión que
siga ese paso al pie de la letra lee «F-006 … RECHAZADA» y se va a rehacer una
feature cerrada. Es exactamente el fallo que la memoria externa existe para
evitar.

**En descargo del implementer:** las secciones obsoletas **vienen heredadas de
`dev`** (`git show dev:progress/current.md` las trae igual: ya estaban rancias
allí). F-007 no las introdujo; reescribió la cabecera y las dejó estar. Pero
C2 evalúa el destino, no el camino, y el destino se contradice.

## 15 · T14 — ejecutada durante esta review, y su tabla se quedó atrás

**T14 se ejecutó mientras yo revisaba.** A media review aparecieron cambios en
el árbol que no eran míos: `tasks.md` con **T14 marcada `[x]`**,
`progress/impl_F-007.md` con una sección nueva al final y `features.json` con
una feature más. Confirmado además en el sistema: el proceso **PID 57996**,
arrancado a las **11:43:15**, es
`python dev_server.py --port 5173 --api http://localhost:7073` — el front del
humano, corriendo. *(No lo he tocado.)*

**Resultado, en palabras del humano: «funciona a la perfección».** El front
arrancó contra la Function con la remesa real delante. Excelente noticia:
cierra el criterio de aceptación 4 y R36.

De la ejecución salieron, además, tres cosas de valor:

1. **Un defecto de la propia T14**, corregido en `tasks.md`: el comando no
   bastaba. Sin `.\.venv\Scripts\Activate.ps1` entre el `cd` y el `func start`,
   `func` arrastra el `.venv` de la **raíz** —el del arnés— y muere con
   `ModuleNotFoundError: No module named 'pydantic'`, porque `cd` no cambia el
   entorno virtual activo. Bien cazado y bien escrito, con el síntoma de
   `[WinError 10061]` documentado como «la Function no está arrancada».
2. **Tres observaciones de diseño**, dadas de alta como **F-020** (el PDF debe
   mandar en la pantalla). Ninguna es un fallo. Es exactamente para lo que
   sirve una verificación manual.
3. La confirmación de que el ruido de `AzureWebJobsStorage` en local no es un
   fallo.

### Pero la tabla de los ocho puntos sigue entera en `PENDIENTE`

`progress/impl_F-007.md:950-959` — los **ocho** puntos, uno por uno:

```
| 1 | ...semáforo de servicio sale verde...            | PENDIENTE |
| 2 | ...sale el número de partes y la lista           | PENDIENTE |
| 3 | ...nunca más de 6 peticiones a /api/ en vuelo    | PENDIENTE |
| 4 | ...el progreso llega a «M de M»                  | PENDIENTE |
| 5 | ...se ve su PDF y sus campos con la confianza    | PENDIENTE |
| 6 | ...revalidar SIN llamar a /api/extraer ni /firma | PENDIENTE |
| 7 | ...archivar responde 503                         | PENDIENTE |
| 8 | ...en la consola NO aparece ningún DNI           | PENDIENTE |
```

El mismo documento dice, 250 líneas más abajo, que la tarea está ejecutada y
funciona. **Las dos cosas no pueden ser ciertas a la vez.**

Y no es formalismo: **«funciona a la perfección» es el veredicto de quien usa
la pantalla, y no equivale a haber comprobado los puntos 3, 6 y 8**, que no se
ven usando el front —se ven abriendo **DevTools → Red** y **DevTools →
Consola—** y que son precisamente los que verifican lo que más importa:

- **Punto 3** es *la* comprobación visual del **criterio de aceptación 3**
  (nunca más de 6 peticiones en vuelo). Es lo único que cierra el círculo
  entre los tests unitarios de la cola y el navegador real.
- **Punto 6** es R17: revalidar no debe gastar IA.
- **Punto 8** es **R28**: que no haya un DNI en la consola del navegador. Es la
  garantía de datos personales, y no se ve «usando» el front.

Que la pantalla funcione bien es una condición necesaria de los tres, no una
prueba de ninguno.

## 16 · Un incidente del arnés que provoqué yo, y que hay que arreglar

**No es un defecto de F-007.** El código del implementer es correcto. Lo
cuento porque el fallo es del arnés, es genérico y es invisible.

Al reejecutar la campaña de mutación (sección 11) la herramienta se negó a
correr en paralelo —mi `review_F-007.md` sin trackear ensuciaba el árbol— y
tuve que usar `--workers 1`, que **muta los ficheros en el árbol principal** en
vez de en worktrees. Al terminar, la campaña restaura la fuente. Pero **no
invalida el bytecode compilado**, y ahí empezó el problema:

```
$ python -m pytest tests/test_f007_dev_server.py -q
INTERNALERROR> SystemExit: 2
```

Desensamblando el `.pyc` que quedó en `services/postventa-front/__pycache__/`:

```
352 LOAD_CONST   15 ('__main__')
354 COMPARE_OP   55 (!=)          <-- el MUTANTE, no la fuente
```

El último mutante evaluado del fichero fue `if __name__ == "__main__":` →
`if __name__ != "__main__":`. Al restaurar la fuente, el `.pyc` del mutante se
quedó con **el mismo tamaño y el mismo `mtime` que la fuente restaurada**
(ambos `1787218604`), así que Python lo dio por válido y siguió usándolo.
Resultado: en ese árbol, **`import dev_server` ejecutaba `main()` y levantaba
un servidor HTTP de verdad en el 0.0.0.0:5173**. Lo comprobé: se quedó
sirviendo hasta que maté el proceso.

Tres razones por las que esto es feo:

1. **Es invisible.** `__pycache__` está en `.gitignore`, así que `git status`
   sale limpio y `git diff` no enseña nada. El árbol parece intacto.
2. **Envenena a quien venga después.** La suite del front quedó rota en ese
   árbol; sin el desensamblado, el siguiente en pasar por aquí habría estado
   depurando un fantasma.
3. **Le toca justo al reviewer.** El protocolo del reviewer manda escribir el
   informe **de forma incremental**; ese fichero sin trackear es lo que fuerza
   `--workers 1`, que es lo que muta en el árbol principal. La trampa está
   armada para dispararse en cada review que reejecute una campaña.

**Ya está limpio.** Borré `__pycache__` y `tests/__pycache__` del front y
reverifiqué: `python -m pytest -q` → **74 passed**; el fichero aislado →
**30 passed**; `import dev_server` → limpio, `__name__ = 'dev_server'`,
`main()` **no** se ejecuta. Y `bash harness/init.sh` → **exit 0**. La guarda
`if __name__ == "__main__":` de `dev_server.py` **funciona perfectamente**: lo
verifiqué también ejecutando la fuente con un `__name__` postizo.

Propuesta de arreglo en **P4**, más abajo.

---

# Recorrido de CHECKPOINTS.md

## C1 — El arnés está completo y en verde

- `[x]` `bash harness/init.sh` termina con exit code 0. Verificado.
- `[x]` Existen los siete ficheros obligatorios.

## C2 — El estado es coherente

- `[x]` Una sola feature `in_progress` (F-007).
- `[x]` Rama actual `feature/F-007-front`.
- **`[ ]`** `progress/current.md` describe SOLO la sesión activa. **NO**: cinco
  afirmaciones de la sesión anterior contradicen el estado real (sección 14).
  Y ha empeorado durante la review: `features.json` ya va por **20** features
  (F-020 se dio de alta al ejecutar T14) y `current.md` sigue diciendo 18.
- `[x]` Toda feature `done` tiene su resumen en `history.md` (F-001 a F-006).

## C3 — El código respeta arquitectura y convenciones

- `[x]` Arquitectura: **N/A justificado** para lo hexagonal (front sin
  dominio); su equivalente respetado y vigilado por tests (sección 13).
- `[x]` Primera línea con la ruta en los 25 ficheros nuevos.
- `[x]` Sin `print()` de debug, sin TODOs sueltos, sin secretos, sin
  dependencias nuevas.
- `[x]` La unidad de trabajo es el parte, no el fichero.
- `[x]` Nada se archiva sin pasar las validaciones (`cuerpoDeArchivo` lanza).
- `[x]` Lo manuscrito no se descarta: DNI y observaciones se pintan en
  pantalla y viajan íntegros a `/api/validar`; lo que no viaja es al archivo.
- `[x]` «Firmado no es conforme» y «reprocesar no duplica»: **N/A
  justificado**, son reglas del backend (F-004, F-002) y F-007 no toca
  `services/postventa-api/`. El front solo pinta el veredicto que emite el
  backend, sin recalcularlo.
- `[x]` Ningún estado de Sigrid hardcodeado: **N/A justificado**, F-007 no
  habla con Sigrid (es F-008/F-009).
- `[x]` Ningún parte ni PDF con datos personales en git. Verificado sobre el
  diff completo, no solo sobre el árbol.

## C3 bis — Documentos de fuera

**N/A justificado**: F-007 no añade ni modifica ningún fichero de
`docs/referencia/`. El diff no toca esa carpeta.

## C4 — La verificación es real

- **`[ ]`** Cada requisito EARS tiene ≥ 1 test trazable. **NO**: **R5, R6, R19
  y R22** no tienen ninguno, y la tabla de trazabilidad de `requirements.md`
  afirma que sí (sección 12). Los 31 restantes sí, y **todos pasan**.
- `[x]` Los unit tests no tocan red ni BBDD. Verificado con sonda propia
  (sección 10) y por inspección de `tests_js/`.
- `[x]` Las verificaciones `MANUAL (humano)` están listadas. T14 consta en
  `current.md`, en `tasks.md` y en el informe, con sus comandos exactos.
  *(Observación menor: `current.md` remite a `tasks.md` en vez de repetir el
  comando literal. Se da por cumplido.)*

## C4 bis — El rigor declarado se cumple

- `[x]` La feature declara `rigor: "estandar"`, valor válido.
- `[x]` **Fase RED**: trazas reales pegadas para los cinco requisitos
  centrales — T2/T3 (la puerta de cobertura, `[KO] … 0.0% de 114 líneas` →
  `[OK] … 98.3%`), T4, T7 y T8 (`MODULE_NOT_FOUND` con el módulo aún sin
  escribir, más un rojo de aserción real en T8), y T9 con la copia rota
  **fuera del árbol**, tal como pide el propio checkpoint para un entregable
  que es el test. El nivel `estandar` **no** exige RED en todo, y no se le
  reclama.
- `[x]` **Cobertura**: `PUERTA COBERTURA` en `[OK]`, 98,3 % de 116 líneas
  (umbral 80 %). Recalculada por el reviewer: 98 %, faltan las líneas 52 y 188,
  ambas inalcanzables sin socket real.
- `[x]` **Mutación**: `progress/mutacion_F-007.md` existe, generado por la
  herramienta, con totales reales.
- `[x]` **Los muertos están comprobados, no solo contados**: 12,1 s < 5 min →
  **campaña reejecutada entera** por el reviewer, con salida fuera de
  `progress/`. Totales idénticos (20/17/3/0). Árbol limpio después.
- `[x]` Cada superviviente tiene análisis completado; **ninguno en
  `PENDIENTE`**. Nivel `estandar`: **no** se exigen cero supervivientes, y no
  se exigen. Los tres son el mismo mutante equivalente, verificado.
- `[x]` Sección **«Evidencias»** con los cuatro números: tests (158 nuevos /
  1.014 totales), cobertura (98,3 %), mutantes y supervivientes (20 / 3),
  tiempo de suite (front 1,80 s; api 23,31 s; raíz 0,51 s). Todos verificados
  de forma independiente y **todos coinciden**.
- `[x]` Ningún punto de este bloque marcado N/A.

## C4 ter — Rutas sensibles

**N/A y sin nada que justificar**: `harness/rutas_sensibles.json` no existe en
este repositorio (es F-015).

## C5 — La sesión se cerró bien

- **`[ ]`** `tasks.md` con todas las tareas `[x]` y un commit por tarea.
  **Las 16 están `[x]`** —T14 se ejecutó durante esta review y salió bien—,
  pero **la tabla de resultados de T14 sigue con sus ocho puntos en
  `PENDIENTE`** dentro de `progress/impl_F-007.md` (sección 15). Una tarea
  marcada hecha cuya propia lista de comprobación está entera sin rellenar no
  es una tarea cerrada. *(El commit sí existe: `f8bc5ba` «F-007 T14: verificada
  por el humano; F-020 de diseno y el despliegue por delante de Sigrid», hecho
  durante esta review. Lo que falta es el contenido de la tabla, no el
  commit.)*
- `[x]` Sin ficheros temporales ni artefactos sin trackear sospechosos.
  *(Observación: `git worktree list` muestra 16 worktrees huérfanos en
  `%TEMP%\mutacion_F-005_zllkg8wf\` de una campaña de F-005, más uno de agente
  en `.claude/worktrees/`. Están fuera del árbol y no ensucian `git status`,
  pero conviene un `git worktree prune`. No es de F-007.)*
- `[x]` `features.json` refleja el estado real (`in_progress`).

---

# Veredicto y cambios requeridos

**CHANGES_REQUESTED**, por **tres** checkboxes vacíos: **C5** (T14 firmada con
su checklist sin rellenar), **C4** (trazabilidad) y **C2** (coherencia del
estado). Ninguno tiene que ver con el nivel de rigor: C2, C4 y C5 se exigen en
**todos** los niveles, `documental` incluido. **No se pide cambiar ni una línea
de código de producción.**

## Cambios requeridos

### 1. Rellenar la tabla de resultados de T14 (C5) — el más importante

`progress/impl_F-007.md:950-959` tiene los ocho puntos en `PENDIENTE` mientras
`tasks.md` da T14 por `[x]` y el propio informe la da por ejecutada y correcta.
Sustituir cada `PENDIENTE` por lo que se observó de verdad.

**Y si alguno de los ocho no se miró, hay que escribirlo, no rellenarlo.** Los
tres que no se ven usando la pantalla:

- **Punto 3** — DevTools → Red, con la remesa procesándose: **nunca más de 6
  peticiones a `/api/` en vuelo**. Es la comprobación visual del **criterio de
  aceptación 3** y lo único que une los tests de la cola con el navegador real.
- **Punto 6** — DevTools → Red: al revalidar un campo corregido **no** aparecen
  llamadas a `/api/extraer` ni a `/api/firma` (R17).
- **Punto 8** — DevTools → Consola: **ningún DNI ni observación** (R28).

Los tres se comprueban en una sola pasada con la remesa ya cargada, y el front
ya está arrancado (PID 57996). Si el humano prefiere no repetirlo, vale con
anotar «no observado» en esos puntos y decidir si se cierra igual: lo que no
puede quedarse es un `PENDIENTE` debajo de una tarea marcada hecha.

El commit de T14 ya está hecho (`f8bc5ba`), así que esto es una corrección
encima, no una tarea nueva.

### 2. Cerrar la trazabilidad de R5, R6, R19 y R22 (C4)

`specs/F-007-front/requirements.md`, tabla «Trazabilidad requisito → test»,
afirma que R1–R6 y R13–R22 los cubren `tests_js/pipeline.test.js` y
`tests_js/seleccion.test.js`. Para **R5, R6, R19 y R22** eso no es cierto: no
existe ningún test, ni con nombre trazable ni sin él, que los compruebe. Están
implementados, pero solo en `index.html` y `js/app.js`, que el diseño deja sin
tests a propósito.

Vale cualquiera de las dos salidas, a elección del implementer:

- **(a)** Escribir los tests. Para **R19** es lo recomendable: la lógica de
  «primer clic arma, segundo clic dispara» se puede sacar de `app.js` a
  `js/pipeline.js` (o a un módulo propio) y probarla como el resto. Es la
  confirmación que separa un clic de una tanda de subidas a SharePoint, y hoy
  **no la comprueba nada**: ni un test, ni ninguno de los ocho puntos de T14.
- **(b)** Corregir la tabla de trazabilidad para que diga la verdad —«MANUAL
  (humano), T14», como ya hace con R36— **y** añadir R19 y R22 como puntos 9 y
  10 de la lista de T14. Con T14 ya ejecutada, esta salida es casi todo
  documentación: R5 y R22 quedaron de hecho ejercitados en la pasada del humano
  (vio la lista de partes y la respuesta de archivar), y basta con dejarlo
  escrito al rellenar la tabla del cambio 1.

Si se elige (b), dígase en el informe **por qué** estos cuatro se verifican a
mano y R13–R18 y R20–R21 no: la respuesta —«son presentación pura, y la
lógica que hay debajo sí está probada»— es buena, pero tiene que estar escrita.

### 3. Limpiar `progress/current.md` (C2)

Quitar o reescribir las secciones heredadas que contradicen el estado real
(sección 14 de este informe):

- `## Estado del backlog: 18 features` → **20** (F-019 y F-020 se dieron de
  alta después), con `done` = F-001…F-006, `in_progress` = F-007,
  `pending` = F-008…F-020. O mejor: **remitir a `BACKLOG.md`**, que se genera
  solo desde `features.json` y no se queda rancio nunca. Duplicar a mano el
  estado del backlog en `current.md` es lo que ha producido este defecto.
- Borrar `## Lo siguiente: F-006, y lo que hay que saber de Graph`, o
  reducirlo a lo que siga vivo: el **riesgo aceptado de los permisos de Graph**
  y su dueño **F-018**, que no debe perderse.
- Quitar «Mientras el merge no esté hecho, F-006 no debe arrancar en paralelo».

No se toca el resto: «Cómo se mergeó F-005», «Pendiente del humano», «Deuda
declarada», «Apuntes para features futuras», «Contexto del arnés» y las «Cinco
lecciones operativas» son contexto vigente y deben quedarse.

## Lo que NO se pide cambiar

Para que no haya duda al releer este informe:

- **Los 3 supervivientes de mutación se quedan.** Nivel `estandar`, análisis
  correcto, mutante equivalente verificado. Escribir un test de la anchura de
  un rótulo sería empeorar la suite.
- **`app.js` sin tests se queda.** Es una decisión de diseño bien razonada y
  bien defendida con dos guardias estáticas. Lo que se pide es que la spec lo
  **diga**, no que se deshaga.
- **La ausencia de `comando_tests` se queda.** Es deliberada, razonada en el
  `$doc` de `servicios.json` y en `design.md` §8.1, y vigilada por un test. El
  criterio de aceptación 5 pide literalmente «con su `comando_tests`», pero su
  intención —«hoy NADIE comprueba el front»— está cumplida y **verificada por
  el reviewer**: sin `node`, el portero se pone rojo. Desviación documentada y
  aceptada.
- **La suite `api` no se toca.** F-007 no cambia ni un fichero del backend.

---

# Méritos, que los hay y son muchos

No es una feature aprobada a duras penas: es de las más sólidas del
repositorio, y estos dos defectos son de acabado.

1. **El agujero de F-001 está cerrado de verdad, y lo comprobé yo.** Sin
   `node` en el `PATH`, la suite del front **falla en rojo con tres tests**, no
   se salta nada. Y `test_f007_r32_hay_tests_de_javascript_que_ejecutar`
   tapa el hueco de segundo orden: una carpeta `tests_js/` vacía haría que
   `node --test` saliera verde sin probar nada.
2. **Campaña de mutación no exigida en `estandar` para lo que aportó, y hecha
   igual**, con dos pasadas: la primera dio 6 supervivientes, el implementer
   **escribió tests para los tres que eran huecos reales** (commit `b76a3f8`) y
   la segunda bajó a 3, todos equivalentes. Eso es usar la mutación para lo que
   sirve, no para rellenar un informe.
3. **Los tests de la cola son de los buenos**: promesas diferidas controladas a
   mano, **cero relojes reales**, y un contador del máximo simultáneo observado
   sobre las **22 tareas** de una remesa como la de Mirasierra. Un test de
   concurrencia con `setTimeout` habría sido intermitente en otra máquina.
4. **Meta-tests que demuestran que las guardias miran.** El barrido de DNI trae
   su propio test (`_es_dni_inventado`, y un DNI sospechoso compuesto en trozos
   para no dispararse a sí mismo); la guardia de estáticos demuestra su fase
   RED rompiendo una copia del `index.html` **fuera del árbol**. Es la defensa
   contra el test que pasa porque no mira nada.
5. **`traza.js` es un filtro, no una convención.** Recorta a cuatro claves **y**
   exige que sean primitivas, para que un `{valor: "…"}` anidado no se cuele; y
   `console.` está prohibido en `app.js` por un test. Un solo sitio por donde
   sale el registro, y ese sitio vigilado.
6. **`cuerpoDeArchivo` se niega por construcción**, no por `:disabled`: lanza
   si el parte no es apto y si ya está archivado. El doble clic está defendido
   en la lógica, donde debe estar.
7. **El límite inválido lanza en vez de degradar** a «sin límite». Es la
   diferencia entre un bug ruidoso y uno que se come un 429 en silencio.
8. **El informe del implementer no esconde nada**: tres desviaciones respecto a
   la spec, todas explicadas por hechos del entorno (Node 24 y el patrón de
   `--test`; PowerShell 5.1 y `-?`), y dos comprobaciones **de más** que nadie
   le pidió. Los cuatro números de «Evidencias» los verifiqué uno a uno y
   **todos coinciden**.
9. **Ni un fichero del backend tocado**, que era la regla que atravesaba todas
   las tareas.
10. **T14 se ejecutó y salió bien** —«funciona a la perfección»—, y de paso
    corrigió un defecto de la propia tarea (`Activate.ps1`, sin el cual `func`
    arrastra el `.venv` equivocado y muere con `ModuleNotFoundError`) y produjo
    tres observaciones de diseño que ya tienen dueño en **F-020**. Que una
    verificación manual encuentre cosas que ningún test habría encontrado es
    exactamente para lo que existe. Lo único que falta es **anotarla**.

---

# Propuestas de mejora del protocolo (no aplicadas)

Para que las apruebe el humano. Si se aceptan, y por la regla de propagación
de `CLAUDE.md`, las tres viajan a `arnes-base` en el mismo trabajo: ninguna es
específica de este proyecto.

**P1 · La mutación no alcanza a los lenguajes que no son Python, y el informe
no lo dice.** La campaña de F-007 mutó **188 líneas de `dev_server.py`** y
**cero** de las **1.322** de `js/`, donde vive toda la lógica de la feature: la
cola, el cliente HTTP y el pipeline. El informe da «20 mutantes / 17 muertos»
sin advertir que el 88 % del código nuevo ejecutable quedó fuera del alcance
por el lenguaje. No es culpa del implementer —`harness/alcance.py` solo mira `.py`—,
pero un lector desprevenido lee esos totales como si cubrieran la feature.
**Propuesta**: que `harness/mutacion.py` liste en el informe los ficheros del
diff **excluidos del alcance por extensión**, con su recuento de líneas, bajo
un epígrafe «Fuera del alcance de la mutación». Una línea de «1.278 líneas de
`.js` no mutadas: el motor solo muta Python» convierte un silencio en un dato.

**P2 · `CHECKPOINTS.md` C5 choca de frente con las tareas `MANUAL (humano)`.**
Es la **tercera** review seguida (F-005 T18, F-006 T18, F-007 T14) que llega
con la única tarea abierta siendo una que ningún agente puede firmar, y el
reviewer tiene que elegir entre marcar un checkbox vacío que no es culpa de
nadie o mentir. **Propuesta**: que C5 distinga «todas las tareas `[x]`» de
«todas las tareas **automatizables** `[x]`, y las `MANUAL (humano)` listadas
con su comando exacto a la espera del humano». Es justamente **F-017**, ya dada
de alta: esta review es la tercera prueba de que hace falta.

**P3 · La campaña de mutación se niega a correr con el árbol sucio, y el
reviewer siempre lo tiene sucio.** El protocolo del reviewer manda escribir
`progress/review_F-XXX.md` de forma incremental; ese fichero sin trackear basta
para que la campaña paralela aborte con «El árbol principal tiene cambios sin
commitear». La salida obliga a `--workers 1`, que multiplicó el tiempo por 2,4
en una campaña pequeña y lo haría intolerable en una grande.
**Propuesta**: que la comprobación de árbol limpio **ignore los ficheros sin
trackear bajo `progress/`**, que por diseño no participan en el código que se
muta; o que el mensaje sugiera `--workers 1` **y** mencione esta causa
concreta, que es la que se va a dar siempre.

**P4 · La mutación en el árbol principal deja bytecode envenenado, y no se
ve.** Es el incidente de la sección 16, y es el más serio de los cuatro porque
**rompe el árbol de trabajo sin dejar rastro en `git status`**. Con
`--workers 1`, `harness/mutacion.py` muta el fichero en sitio y luego restaura
la fuente, pero el `__pycache__/*.pyc` del mutante sobrevive con el mismo
tamaño y el mismo `mtime` que la fuente restaurada, así que Python lo considera
válido y lo sigue usando. En este caso concreto, el mutante superviviente en
caché era `if __name__ != "__main__":`, de modo que **`import dev_server`
levantaba un servidor HTTP real**. `__pycache__` está en `.gitignore`: ni
`git status` ni `git diff` enseñan nada.

**Propuesta**: que la restauración de cada mutante borre el `.pyc`
correspondiente —o llame a `importlib.invalidate_caches()` y elimine el
`__pycache__` de los ficheros tocados— antes de dar la campaña por terminada.
Alternativa más barata y casi igual de eficaz: ejecutar las suites de la
campaña con `PYTHONDONTWRITEBYTECODE=1`, para que no se escriba ningún `.pyc`
desde un fuente mutado. Y, por si acaso, que la campaña termine con una nota
en el informe recordando borrar `__pycache__` si se usó `--workers 1`.

**P3 y P4 se disparan juntos y por la misma causa**: el informe incremental del
reviewer ensucia el árbol → la campaña obliga a `--workers 1` → `--workers 1`
muta en sitio → el bytecode queda envenenado. Arreglar P3 (ignorar los ficheros
sin trackear de `progress/`) evita P4 en el caso del reviewer; arreglar P4 lo
evita siempre. **Merecen ir juntas a `arnes-base`.**

---

# 17 · Cierre — segunda pasada (2026-08-20)

Los tres cambios están hechos. **Los he verificado uno a uno**, no leído del
resumen del líder.

**Entorno:** `bash harness/init.sh` → **exit 0**, dos servicios, `PUERTA
COBERTURA 98,3 % (114/116)`. Árbol limpio salvo este informe. Seis commits
nuevos sobre `124e4b6`.

## Cambio 1 · La tabla de T14 (C5) — `[x]` RESUELTO

`d786b86`. **Ni un `PENDIENTE`**: los diez puntos con resultado real
(`progress/impl_F-007.md:951-961`), incluidos los dos que yo pedí añadir (9 y
10, R19 y R22). Los tres que solo se ven en DevTools tienen su sección de
evidencia propia.

**Punto 3 · ¿basta una lectura de la cascada para el criterio de aceptación 3?
Sí, y lo digo porque se me preguntó expresamente.** Razones:

1. **La cota exacta ya está demostrada**, y no por observación: `cola.test.js`
   mide el **máximo simultáneo observado** sobre 22 tareas con límite 3, de
   forma determinista y sin relojes. Eso es más fuerte que cualquier captura.
2. **El cableado está verificado por lectura**: `app.js:151-155` alimenta la
   cola con `CONCURRENCIA_PARTES` y una tarea por parte; `procesarParte` lanza
   `extraer`+`firma` en paralelo y `validar` después. 3 × 2 = 6.
3. **Lo que le faltaba al conjunto era justo lo que aporta la captura**: que en
   un navegador real, con la remesa real, el cableado se comporte como dice el
   código. «Tandas escalonadas de unas seis barras solapadas, con huecos entre
   grupos» **falsa directamente** el modo de fallo que nombra el criterio —«una
   remesa larga dispara N peticiones a la vez»—, y confirma el patrón
   `extraer`+`firma` en paralelo, `validar` después.

Un recuento instante a instante mediría otra vez, y peor, lo que el test
unitario ya clava. **Las tres evidencias juntas cierran el criterio**; ninguna
lo haría sola. Y que se anotara la limitación en vez de venderla como un
recuento exacto **aumenta** mi confianza en el resto de la tabla: un informe que
distingue lo que vio de lo que dedujo es un informe fiable.

**Punto 6**: la traza `{hash: 'e2cd481b…', paso: 'validar', estado: 'ok',
http: 200}`, **un solo registro y con paso `validar`**, es el argumento
correcto: un reprocesado habría dejado registros de `extraer` y `firma` al
lado. R17 verificado en el navegador.

**Punto 8**: esa misma traza con **exactamente cuatro claves** demuestra el
filtro de `traza.js` en ejecución, no solo en test. Y el apunte de que el
`hash` es el SHA-256 del contenido —«identifica al parte sin nombrarlo»— es
correcto: no es dato personal. R28 verificado.

## Cambio 2 · Trazabilidad (C4) — `[x]` RESUELTO

`788751a`, `9a6db89`, `bc3a435`. Se tomó la **salida mixta**, que era la
correcta:

- **R19 con test de verdad.** La confirmación sale de `app.js` a
  `js/confirmacion.js`, y `app.js` la consume vía `window.Confirmacion`
  (`armar`, `pendiente`, `resolver`, `cancelar`) sin lógica propia. **13 tests**
  en `tests_js/confirmacion.test.js`, y no son de trámite: cubren el primer clic
  que no dispara, el segundo que sí, el desarme posterior, la **caducidad** de
  una confirmación olvidada, el **borde exacto** de la ventana, un **reloj que
  va hacia atrás**, un **estado corrupto** y que `resolver` **no muta** lo que
  recibe. Es más de lo que pedí.
- **Fase RED de R19, y de la buena.** No se conformó con el
  `MODULE_NOT_FOUND`: hay un **«Rojo 2 — de aserción, que es el que vale»** con
  un **stub trampa** que devuelve siempre `true`, para comprobar que 8 de los 13
  tests muerden de verdad. Es la misma disciplina de los meta-tests del barrido
  de DNI, y es lo que separa un test de un adorno.
- **R5, R6 y R22 → `MANUAL (humano), T14`** en la tabla de trazabilidad, con el
  porqué escrito, igual que ya hacía R36. La tabla ahora **dice la verdad**,
  que era el defecto de fondo.

Verificado además que la guardia de estáticos **no se quedó atrás**:
`ORDEN_CANONICO` incluye ya `js/confirmacion.js` en su sitio (séptimo, antes de
`app.js`), y el `<script>` está en `index.html:297`. Una guardia de orden que
dejara fuera el módulo nuevo habría sido una regresión silenciosa.

**Suite JS: 97 tests, 97 pass, 0 fail, 0 skipped** (eran 84). Barrido propio
sobre los dos ficheros nuevos: **cero** `localStorage`/`sessionStorage`/
`indexedDB`/`document.cookie`, **cero** `console.`, **cero** DNI, cabecera con
la ruta en la primera línea.

## Cambio 3 · `progress/current.md` (C2) — `[x]` RESUELTO

`dfb9029`. La sección ya **no duplica el backlog a mano**: remite a
`BACKLOG.md`, que se genera desde `features.json` y lo regenera `init.sh`. Es
la solución de raíz, no el parche —el defecto no era el número equivocado, era
mantener a mano una copia de algo generado—, y el propio texto deja escrita la
lección. La sección de F-006 se ha reducido a lo único vivo: el riesgo aceptado
de los permisos de Graph, con **F-018** como dueña. Se conserva lo que debía
conservarse.

## Observación menor, que NO bloquea

`progress/impl_F-007.md:924` conserva el encabezado
`## T14 · Verificación MANUAL (humano) — PENDIENTE` y el párrafo «Queda
pendiente del humano», justo encima de la tabla que ya está entera en **OK**, y
con el `Terminal A` sin la línea de `Activate.ps1` que sí se corrigió en
`tasks.md`. El documento no engaña —la evidencia de DevTools va debajo y la
sección 1236 la da por ejecutada—, pero conviene ajustar esas tres líneas la
próxima vez que se toque el fichero. **No es motivo de nada**: mi objeción era
la checklist en blanco bajo una tarea firmada, y esa está resuelta.

## Recorrido final de los checkboxes que estaban vacíos

| Checkpoint | Primera pasada | Ahora |
|---|---|---|
| **C2** · `current.md` solo la sesión activa | `[ ]` | **`[x]`** |
| **C4** · cada requisito con test trazable | `[ ]` | **`[x]`** — R19 con 13 tests; R5, R6, R22 y R36 declarados MANUAL/T14 con su motivo; R33 y R37 justificados |
| **C5** · tareas `[x]` y checklist cerrada | `[ ]` | **`[x]`** — 16/16, tabla de T14 con diez resultados reales |

**C1, C3, C3 bis, C4 bis y C4 ter ya estaban en verde** en la primera pasada y
nada de esta tanda los toca: el portero sigue en exit 0, la cobertura en
98,3 %, y la campaña de mutación que reejecuté (20/17/3/0) sigue siendo válida
—los tres supervivientes son del rótulo de `dev_server.py`, que nadie ha
tocado—.

# VEREDICTO FINAL: **APROBADO**

Con dos apuntes que no condicionan la aprobación pero que el humano debería
tener delante al cerrar:

1. **F-020 recoge las tres observaciones de diseño** de T14 (el PDF debe mandar
   en la pantalla). El front es correcto; es trabajo de usabilidad, ya con
   dueño.
2. **Las cuatro propuestas de arnés (P1–P4) siguen sin aplicar** y esperan
   decisión. **P4 es la urgente**: la campaña de mutación con `--workers 1`
   deja bytecode envenenado en `__pycache__` que rompe la suite sin que
   `git status` lo enseñe. Lo sufrí en esta review (sección 16) y volverá a
   pasarle a quien reejecute una campaña con el árbol sucio, que es la
   situación normal del reviewer.

Y no lo hago yo, por regla: **ni `git push`, ni PR, ni merge a `dev`.** Eso lo
decide el humano.

---

*Informe cerrado el 2026-08-20 tras dos pasadas. Ninguna línea de código del implementer fue
modificada por el reviewer; la única escritura fue este fichero.*
