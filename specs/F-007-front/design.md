<!-- specs/F-007-front/design.md -->
# F-007 · Front de carga y revisión — Diseño técnico

> Nivel de rigor: **`estandar`**. Se diseña para eso: tests trazables, fase
> RED en lo central (la cola y el pipeline), cobertura ≥ 80 % de las líneas
> cambiadas y campaña de mutación con supervivientes analizados.

## 1 · Punto de partida: lo que YA existe y no se redescubre

El esqueleto del front está escrito y verificado en la rama
`feature/F-007-front` (commit `cdcd79c`, «F-001: esqueleto del monorepo…»).
Salió de F-001 porque su `dev_server.py` hundía la puerta de cobertura, y es
justo el problema que resuelve §9.

Se recupera con **un solo comando**, sin reescribir nada:

```
git checkout feature/F-007-front -- services/postventa-front
```

Trae seis ficheros: `index.html`, `css/styles.css`, `js/config.js`,
`js/app.js`, `dev_server.py`, `staticwebapp.config.json`.

**Decisiones ya tomadas ahí dentro. No se rediscuten, y romperlas es un bug:**

| Decisión | Por qué | Quién la vigila |
|---|---|---|
| Los scripts **propios** van al final del `<body>` **sin `defer`** | Con `defer` Alpine arrancaría antes de que exista la función del `x-data` y la pantalla queda muerta | `tests/test_f007_estaticos.py` |
| Alpine va **con `defer`** en el `<head>` y con **versión fija** `3.14.1` | Así se ejecuta después de nuestros scripts; sin versión fija, un cambio del CDN rompe el front | ídem |
| **Nada de `<script type="module">`** | Un módulo se difiere **implícitamente**: sería el mismo fallo que `defer` por otra puerta | ídem |
| El proxy del `dev_server` apunta a **7073** | Es el puerto de `func start` en este proyecto | ídem |
| `staticwebapp.config.json` lleva `<TENANT_ID>` como **marcador** | El ID de inquilino no se versiona (regla dura de `CLAUDE.md`). Se resuelve en el despliegue, que es **F-010** | ídem |
| `baseApi: "/api"` | Mismo origen en local (proxy) y en la SWA (Function enlazada): sin CORS y sin URL que mantener | ídem |

Patrón de referencia: **`front-nominas`** (HTML + Tailwind CDN + Alpine +
`dev_server.py`). De ahí salen la forma de la zona de carga (`drop`,
`acceptFiles`) y la estructura de `js/`. Lo que `front-nominas` **no** tiene y
aquí hace falta es el limitador de concurrencia: allí es una llamada, aquí son
22 partes.

## 2 · Ficheros

### 2.1 · A crear

| Ruta | Qué es |
|---|---|
| `services/postventa-front/js/cola.js` | **Limitador de concurrencia**. Función pura `ejecutarConLimite(tareas, limite)`: como mucho `limite` tareas vivas, el resto esperando; un error no para las demás. Sin `fetch`, sin DOM, sin Alpine. |
| `services/postventa-front/js/api.js` | **Cliente de los seis endpoints**. Una función por endpoint (`salud`, `trocear`, `extraer`, `firma`, `validar`, `archivar`), más `peticion()` con timeout (`AbortController`), reintento con backoff y clasificación del error. `fetch` y el temporizador se **inyectan** (parámetros con valor por defecto) para poder probarlo sin red. |
| `services/postventa-front/js/pipeline.js` | **Orquestación de un parte**: `procesarParte(parte, api)` → extraer + firma en paralelo, luego validar; y `cuerpoDeValidacion(extraccion, firma)`, `cuerpoDeArchivo(parte)`, `esArchivable(validacion)`. Sin DOM. |
| `services/postventa-front/js/confirmacion.js` | **La confirmación en dos pasos antes de archivar (R19)**: `armar(ahoraMs)`, `pendiente(estado)`, `resolver(estado, ahoraMs)`, `cancelar()`. Lógica pura, con el reloj inyectado. *(Añadido en la review de F-007: vivía en `app.js`, donde no lo comprobaba nadie, y es lo único que separa un clic accidental de una tanda de subidas reales a SharePoint.)* |
| `services/postventa-front/js/traza.js` | **El único registro permitido**: `traza({hash, paso, estado, http})`. Descarta cualquier clave que no sea una de esas cuatro (R28). |
| `services/postventa-front/js/seleccion.js` | Filtrado de la selección de ficheros: `filtrarAdmitidos(ficheros)` → `{admitidos, descartados}`; y `formDataDeRemesa(ficheros)` con nombres de campo distintos (R4). |
| `services/postventa-front/tests/conftest.py` | Pone la raíz del front en `sys.path` y monta la **guardia de red** de la suite (R33). Vive dentro de `tests/`, que el arnés excluye del alcance. |
| `services/postventa-front/tests/test_f007_dev_server.py` | Tests de `dev_server.py` con dobles: routing `/api/*` vs estático, saneo de cabeceras, 502 en JSON, argumentos del CLI, arranque sin `index.html`. |
| `services/postventa-front/tests/test_f007_js.py` | **Puente**: lanza `node --test tests_js/` y falla si `node` no está o si algún test JS falla (R32). |
| `services/postventa-front/tests/test_f007_estaticos.py` | Contrato de los ficheros estáticos: scripts propios sin `defer` y al final del `body`, Alpine con versión fija, ningún `type="module"`, marcador `<TENANT_ID>` intacto, puerto 7073. |
| `services/postventa-front/tests/test_f007_declaracion.py` | El servicio del front está declarado en `harness/servicios.json` y su declaración apunta a esta carpeta (R31). |
| `services/postventa-front/tests/test_f007_sin_datos_reales.py` | Ningún fixture ni fichero del front contiene un patrón de DNI ni un PDF real (R30). |
| `services/postventa-front/tests/test_f007_documentacion.py` | El `README.md` del front documenta la decisión de §9 (R35). |
| `services/postventa-front/tests_js/cola.test.js` | R7–R12. |
| `services/postventa-front/tests_js/api.test.js` | R23–R27. |
| `services/postventa-front/tests_js/pipeline.test.js` | R8, R13–R18, R20–R21, R29. |
| `services/postventa-front/tests_js/confirmacion.test.js` | R19. |
| `services/postventa-front/tests_js/seleccion.test.js` | R1–R4. |
| `services/postventa-front/tests_js/traza.test.js` | R28. |
| `services/postventa-front/README.md` | Cómo se arranca en local, cómo se prueba y **la decisión de §9**. |
| `services/postventa-front/dev_front.ps1` | Arranca el `dev_server` con una sola línea, para el humano (PowerShell). |
| `specs/F-007-front/*` | Esta spec. |

### 2.2 · A modificar

| Ruta | Qué cambia |
|---|---|
| `services/postventa-front/index.html` | Se sustituye el bloque «Estado del servicio» por la pantalla real (zona de carga, progreso, lista de partes, panel de detalle con PDF). Se añaden los cinco `<script>` nuevos al final del `body`, **sin `defer`**, en orden de dependencia: `config`, `traza`, `cola`, `api`, `seleccion`, `pipeline`, `confirmacion`, `app`. |
| `services/postventa-front/js/config.js` | Se añaden `CONCURRENCIA_PARTES: 3`, `TIMEOUT_PETICION_MS: 180000`, `REINTENTOS: 2`, `ESPERAS_MS: [1000, 3000]`, `UMBRAL_CONFIANZA: 50`. `baseApi` no se toca. |
| `services/postventa-front/js/app.js` | Pasa de comprobar `/health` a ser el estado de Alpine: selección, arranque de la cola, progreso, parte seleccionado, edición, revalidación, archivo. **Solo pegamento**: la lógica vive en los módulos de §2.1, que son los que se prueban. |
| `harness/servicios.json` | Se declara el servicio del front (§8.1). |
| `progress/current.md` | Estado de la sesión. |

### 2.3 · Ficheros que NO se tocan

- **Todo `services/postventa-api/`.** Los seis endpoints están cerrados. Si al
  implementar aparece la tentación de cambiar un contrato, **se para y se
  pregunta**: sería otra feature.
- `services/postventa-front/css/styles.css` — vale tal cual.
- `services/postventa-front/staticwebapp.config.json` — es de **F-010**. En
  particular, el marcador `<TENANT_ID>` **no se resuelve aquí**.
- `services/postventa-front/dev_server.py` — se recupera y se **prueba**, pero
  no se reescribe (§9).
- `harness/*.py`, `harness/init.sh`, `CHECKPOINTS.md`, `specs/SPECS.md` — el
  arnés genérico no se toca en F-007 (§9, opción O2 descartada).
- `tests/` de la raíz — `test_servicios_declarados.py` ya hace su trabajo.

## 3 · Capas

El front no es hexagonal —es una pantalla—, pero se organiza con la misma
idea, que es lo que lo hace probable sin navegador:

```
js/cola.js       lógica pura        sin fetch, sin DOM   ← el 80 % de los tests
js/pipeline.js   orquestación       recibe `api` inyectada
js/seleccion.js  lógica pura        sin DOM (recibe File[])
js/traza.js      lógica pura
js/confirmacion.js  lógica pura     el doble clic antes de archivar (R19)
js/api.js        adaptador HTTP     `fetch` y timers inyectables
js/app.js        pegamento Alpine   NO se prueba: no debe tener lógica
```

Regla de oro del diseño: **si algo merece un test, no vive en `app.js`.** Ese
fichero solo mueve estado de Alpine y llama a los módulos.

## 4 · Flujo de la pantalla

```
inactivo ──(soltar / elegir carpeta)──▶ seleccionado
   ▲                                        │ confirmar
   │                                        ▼
   │                                    troceando  (POST /api/split)
   │                                        │ 200
   │                                        ▼
   └───(reiniciar)───────────────────── procesando  (N de M, cola de 3)
                                            │ todos terminados
                                            ▼
                                        revision    ← edición + revalidar
                                            │ confirmar archivo
                                            ▼
                                        archivando  (cola de 3)
                                            │
                                            ▼
                                         resumen
```

Estado por parte: `pendiente → leyendo → validando → listo | error`. En
`listo`, además, el semáforo (`verde` / `ambar` / `rojo`) y, tras archivar,
`archivado` o `error_archivo`.

Lo que se ve de cada parte en la lista: `hash` corto, origen, páginas de
origen, semáforo y motivos. Lo que se ve al abrirlo: los nueve campos
editables con su confianza, la clasificación de la firma, los avisos y el PDF
del parte en un `<iframe>` con `URL.createObjectURL(blob)` construido desde
`contenido_b64`. El objeto URL se **revoca** al cambiar de parte: 22 blobs
vivos es memoria que no vuelve.

## 5 · El límite de concurrencia (criterio de aceptación 3)

**Valor: 3 partes en curso a la vez.** Constante `CONCURRENCIA_PARTES` de
`js/config.js`, no un número escondido en el pipeline.

Los números de los que sale:

1. **La remesa real de Mirasierra son 22 partes** y cada parte cuesta **dos
   llamadas a IA** (`/api/extraer` y `/api/firma`, que van en paralelo a
   propósito: componerlas sumaría dos timeouts de 120 s y la Function corta a
   los 230 s). Son **44 llamadas de IA** por remesa.
2. **3 partes × 2 llamadas = 6 peticiones vivas.** Seis es exactamente el
   máximo de conexiones simultáneas por origen que abre un navegador sobre
   HTTP/1.1, que es lo que sirve el `dev_server`. Pedir más no acelera nada:
   el navegador las encola igual, pero **sin que el usuario lo vea** y con el
   temporizador de R12 corriendo.
3. **En local hay un solo worker.** `func start` levanta un proceso de worker
   de Python; lanzar 22 peticiones a la vez contra él no es paralelismo, es
   una cola invisible que acaba en timeouts.
4. **Cuota del proveedor.** 44 llamadas multimodales disparadas de golpe son
   la forma más rápida de comerse un 429 y convertir una remesa entera en
   errores transitorios.
5. **Sirve para algo**: con 3 en curso la barra de progreso avanza de verdad y
   el tiempo de pared baja a un tercio del serie, sin ninguno de los efectos
   de arriba.

Por qué **no** otras opciones: **1** (serie) es honesto pero lento —22 partes
en fila, con llamadas que pueden tardar decenas de segundos—; **6 o más**
cruza el punto 2 y empeora el 3 y el 4; **sin límite** es literalmente lo que
el criterio de aceptación prohíbe.

Forma del limitador, que es lo que se prueba:

```js
// ejecutarConLimite(tareas, limite, alTerminar) -> Promise<Resultado[]>
//   tareas: array de funciones que devuelven una promesa
//   limite: entero >= 1
//   alTerminar(indice, resultado): se llama al acabar cada tarea (progreso)
// Devuelve un resultado por tarea, EN EL ORDEN DE ENTRADA, cada uno
// {ok: true, valor} o {ok: false, error}. Nunca rechaza: un parte roto no
// puede tumbar la remesa (R10).
```

Lo que los tests de `cola.test.js` comprueban, con tareas falsas y promesas
controladas a mano (nada de relojes reales): que el **máximo simultáneo
observado nunca pasa del límite**; que con `limite` mayor que el número de
tareas no se rompe; que un error deja pasar a los siguientes; que el orden de
resultados es el de entrada aunque terminen desordenadas; que `alTerminar` se
llama exactamente una vez por tarea; y que `limite < 1` es un error de
programación, no un «sin límite» silencioso.

**La misma cola se usa para archivar** (R20): otra fase, mismo límite, misma
implementación.

## 6 · Contrato con el backend

Ninguno de estos endpoints se toca. La tabla es lo que el front puede esperar:

| Endpoint | Envía | Devuelve 200 | Errores |
|---|---|---|---|
| `GET /api/health` | — | `servicio`, `version`, `entorno`, `estado` | — |
| `POST /api/split` | `multipart`: `fichero_0…N` | `total_partes`, `partes[]` (`hash`, `origen`, `paginas_origen`, `modo_deteccion`, `avisos`, `contenido_b64`), `avisos` | **400** sin PDF utilizable (trae `error` + `avisos`), **413** fuera de límite |
| `POST /api/extraer` | `multipart`: fichero + `hash` | `hash_parte`, `campos{9}` (`valor`, `confianza_pct`), `traza`, `avisos` | **400** sin fichero, **413** parte > 15 MB, **502** el modelo no dio nada utilizable |
| `POST /api/firma` | `multipart`: fichero + `hash` | `hash_parte`, `firma{clasificacion, confianza_pct}`, `traza`, `avisos` | igual que extraer |
| `POST /api/validar` | JSON `{extraccion, firma}` **verbatim** | `hash_parte`, `veredicto`, `destino`, `motivos[]`, `firma`, `observaciones`, `avisos` | **400** con el texto de qué falta |
| `POST /api/archivar` | `multipart`: fichero + `hash`, `codigo_obra`, `numero_incidencia`, `veredicto`, `destino` | `hash_parte`, `nombre_fichero`, `carpeta`, `estado`, `web_url`, `avisos` | **400** cuerpo incompleto, **409** no apto o no nombrable, **503** este entorno no archiva, **502** el proveedor falló |

Dos cosas que el front **no** puede hacer, y que el backend ya defiende:

- **Montar el cuerpo de `/api/validar` a mano.** Solo se admite el cuerpo tal
  y como lo emiten los otros dos endpoints. El front guarda las dos respuestas
  íntegras y solo cambia `campos[x].valor` (y su confianza, D3) cuando una
  persona edita.
- **Mandar de más a `/api/archivar`.** El endpoint solo acepta los cinco
  campos; el DNI y las observaciones **no viajan** (R29). El propio handler lo
  documenta: pedir los nueve campos obligaría a reenviar el dato personal en
  cada archivo.

## 7 · Manejo de errores

Clasificación única, en `js/api.js`, y una sola forma de error hacia arriba:
`{tipo, http, mensaje}` con `tipo ∈ {transitorio, peticion, no_apto,
entorno, desconocido}`.

| Situación | `tipo` | ¿Reintenta? | Qué ve el usuario |
|---|---|---|---|
| Fallo de red, `AbortError` por timeout, **502** | `transitorio` | Sí: 2 veces, esperas 1 s y 3 s (R23) | «No se pudo contactar con el servicio, reintentando…» y, si agota, el parte queda reintentable |
| **400** | `peticion` | No | El `error` del backend, tal cual |
| **413** | `peticion` | No | «El parte no cabe en una petición» + a revisión manual |
| **409** en archivar | `no_apto` | No | El `error` del backend; el parte no se archiva |
| **503** en archivar | `entorno` | **No** | «Este entorno no archiva» — es la puerta de entorno de F-006, no un fallo (R25) |
| Respuesta no-JSON | `desconocido` | No | «Respuesta inesperada del servicio (HTTP nnn)» (R26) |

El **503 merece pantalla propia**, no un error rojo genérico: desde un puesto
de trabajo es el comportamiento **correcto** y esperado (`ARCHIVO_HABILITADO`
está apagado por defecto). Un implementador que lo pinte como fallo hará que
alguien intente «arreglarlo» tocando la puerta de entorno, que es exactamente
lo que no puede pasar.

El backoff no usa `setTimeout` directamente: `api.js` recibe un `esperar(ms)`
inyectable, y los tests le pasan uno que resuelve al momento. Así R23 se
prueba en milisegundos y sin relojes falsos.

## 8 · Cómo se prueba un front estático sin cadena de build

Es el criterio de aceptación 5, y la pregunta real es **con qué**. La
respuesta, proporcionada al rigor `estandar`:

- **`node --test`** para el JavaScript. Viene **dentro de Node** desde la 18
  (aquí hay Node 24): sin `package.json`, sin `npm install`, sin dependencias,
  sin `node_modules` en el repositorio. Los módulos se escriben en CommonJS
  clásico y se exponen en las dos direcciones:

  ```js
  if (typeof window !== "undefined") { window.Cola = { ejecutarConLimite }; }
  if (typeof module !== "undefined" && module.exports) { module.exports = { ejecutarConLimite }; }
  ```

  El navegador los carga como `<script>` de siempre (sin `defer`, §1) y Node
  los carga con `require`. **Cero herramientas nuevas.**

- **pytest** para `dev_server.py`, para el contrato de los ficheros estáticos
  y como **puente** al `node --test`. El puente hace que el front sea **un
  solo servicio** para el arnés, con una sola forma de ejecutarse.

- **Nada de Playwright, Jest, Vitest, Karma ni un navegador headless.** Para
  `estandar`, y para una pantalla cuya lógica está deliberadamente fuera del
  DOM, montar un navegador en el portero cuesta minutos por arranque y trae
  una cadena de dependencias que hoy no existe. Lo que quedaría sin cubrir
  —que el `x-data` pinta lo que debe— lo cubre la verificación **MANUAL**
  (T14), que es donde de verdad se ve.

### 8.1 · Declaración en `harness/servicios.json`

```json
{
  "nombre": "front",
  "ruta": "services/postventa-front",
  "lenguaje": "python"
}
```

- **`lenguaje: "python"`** y no `"otro"`: el front tiene un `.py` de verdad
  (`dev_server.py`) y el arnés solo mide cobertura y muta ficheros Python. Con
  `"otro"` la suite se ejecutaría por `comando_tests`, pero `dev_server.py`
  seguiría contando como **no medido** en la puerta de cobertura, que es
  exactamente el problema que expulsó al front de F-001. Declararlo Python es
  lo que hace que la puerta lo mida.
- **Sin `venv`**: el front no tiene dependencias (`dev_server.py` es solo
  biblioteca estándar). Sin `venv` el arnés usa el intérprete que corre
  `init.sh`, que es el de la raíz y ya trae `pytest` y `coverage`
  (`requirements-dev.txt`). Declarar un `venv` que no existe haría fallar el
  portero; declarar uno vacío sería mantener un entorno para nada.
- **Sin `comando_tests`**: con `lenguaje: "python"` el arnés ejecuta `pytest`
  en la carpeta del servicio, y ahí dentro está el puente a `node --test`.

Efectos inmediatos, todos deseados: `init.sh` ejecuta la suite del front
(§7 bis), escribe `services/postventa-front/coverage.json`, la puerta de
cobertura mide las líneas nuevas de `dev_server.py` y la campaña de mutación
juzga esos mutantes **con la suite del front**.

## 9 · `dev_server.py` frente a la puerta de cobertura (criterio 6)

### El problema, exacto

`harness/alcance.py` considera código de producción **cualquier `.py`** cuya
ruta no lleve un segmento `tests`, `specs`, `progress` o `docs`. No hay lista
de exclusiones, ni por fichero ni por servicio. `dev_server.py` llega **entero
como fichero nuevo** frente a `dev` (~130 líneas), así que sus líneas entran
en el alcance de F-007 hagamos lo que hagamos: **no hay opción «no tocarlo»**.
Sin tests, la puerta lo cuenta como no cubierto y `init.sh` se pone en rojo.
Eso es lo que pasó en F-001.

### Las opciones reales

| | Opción | Coste | Riesgo |
|---|---|---|---|
| **O1** | **Probar `dev_server.py` de verdad**: suite pytest propia del front, con dobles y sin red | ~150 líneas de test para un script que solo se usa en desarrollo; sus mutantes entran en la campaña | Bajo. No toca el arnés |
| **O2** | **Añadir exclusiones configurables al arnés** (p. ej. `harness/exclusiones.json`, o un campo por servicio) | Tocar código genérico del arnés + sus tests + **portarlo a `arnes-base` en el mismo trabajo** (regla de propagación de `CLAUDE.md`) | Alto. Abre una puerta que se ensancha sola: cualquier fichero incómodo pasa a ser «script de desarrollo». Y es trabajo de **otro producto** (`arnes-base`), no de F-007 |
| **O3** | **Esconderlo** en una carpeta ya excluida (`tests/`, `docs/`) | Casi cero | Alto. Es mentira: un servidor de desarrollo no es documentación ni un test. Y enseña el truco: «si no lo puedes probar, muévelo a `tests/`» |
| **O4** | **Adelgazar `dev_server.py`** hasta que casi no tenga líneas | Reescribir algo que ya funciona y está verificado | Medio. No elimina el problema, solo lo encoge; y rompe la única pieza que hoy funciona |
| **O5** | Cerrar la feature con el portero en rojo y autorización del humano | Cero | Inaceptable: `CLAUDE.md` prohíbe cerrar sin `init.sh` en verde |

### Recomendación: **O1**, y creo que es claramente superior

Tres razones:

1. **Cierra dos criterios con el mismo trabajo.** El criterio 5 pide que
   alguien compruebe el front; el 6 pide decidir qué hacer con
   `dev_server.py`. O1 responde a los dos con la misma suite. O2 y O3 resuelven
   el 6 y dejan el 5 igual de abierto.
2. **`dev_server.py` no es un script cualquiera.** Es el único sitio donde se
   reproduce el comportamiento de la SWA en producción: proxy al mismo origen,
   cabeceras reenviadas, `x-ms-client-principal`. Si se rompe, el desarrollo
   local deja de parecerse al despliegue y nadie se entera hasta F-010. Es
   código que **merece** tests, no código al que haya que perdonárselos.
3. **Es barato y no toca el arnés.** El fichero no abre red por sí mismo: la
   conexión se crea en `_proxy` a través de `http.client.HTTP(S)Connection`,
   que en los tests se sustituye por un doble. El routing, el saneo de
   cabeceras (`host`, `connection` fuera), el 502 en JSON, el CLI y el arranque
   sin `index.html` se prueban sin levantar un socket.

**No bloquea**: si el humano prefiere O2, es una feature de `arnes-base` y
F-007 no la espera. Queda como **D1**.

**Lo que se escribe, y dónde** (R35): esta sección §9 y un resumen en
`services/postventa-front/README.md`, para que quien abra el front dentro de
seis meses no repita la pregunta.

## 10 · Límite de microservicio

F-007 vive **entero** dentro de `services/postventa-front/`, más la
declaración en `harness/servicios.json`. No toca `services/postventa-api/`.
Tres fronteras que aparecen al diseñar y que **no** se cruzan aquí:

1. **Persistencia.** F-005 dejó `RepositorioPartesPort` con
   `guardar_remesa`, `guardar_parte`, `guardar_validacion` y
   `cola_validacion_humana`, pero **el único endpoint que escribe hoy es
   `/api/archivar`** (guarda su traza). No hay endpoint HTTP para persistir la
   remesa, los partes ni las validaciones. **Consecuencia asumida en F-007:
   el trabajo vive en la pestaña del navegador**; si se recarga, se pierde y
   hay que volver a subir la remesa. Añadir esos endpoints es del servicio
   `postventa-api`, no del front: se propone como feature aparte (**D4**).
2. **Autenticación.** `/.auth/me`, el grupo de Entra y el `<TENANT_ID>` son
   **F-010**. En local el backend va con `AUTH_DISABLED`.
3. **Cierre en Sigrid.** El botón de cerrar la incidencia no se pinta: F-009
   depende de un endpoint nuevo en `sigrid-api`, que es **otro repositorio**.

## 11 · Datos personales en pantalla

Los partes traen **DNI y observaciones manuscritas** de clientes reales.

- **Sí se enseñan en pantalla**, los dos: quien revisa necesita ver el
  `dni_cliente` para corregir una lectura y las `observaciones` para decidir
  si el parte se cierra (`docs/ARCHITECTURE.md`, semántica 3 bis). Ocultarlos
  haría inútil la revisión.
- **No se registran en ningún sitio.** Ni consola, ni `localStorage`, ni
  `sessionStorage`, ni URL, ni telemetría. El único registro que el front
  emite pasa por `js/traza.js`, que acepta **cuatro claves** (`hash`, `paso`,
  `estado`, `http`) y tira el resto. Es un filtro, no una convención: lo
  prueba `traza.test.js`.
- **No viajan de vuelta al archivar**: `/api/archivar` recibe cinco campos y
  ninguno es personal (R29).
- **No entran en el repositorio**: los fixtures son PDFs mínimos construidos
  en el propio test. Ningún parte de `muestras/` se copia a `tests/`.
- El PDF se muestra desde un **blob en memoria**, nunca desde una URL con el
  contenido dentro, y el objeto URL se revoca al cerrar el parte.

## 12 · Riesgos y alternativas descartadas

| Riesgo | Mitigación |
|---|---|
| La lógica acaba en `app.js` y no la prueba nadie | Regla explícita de §3; los tests están escritos contra los módulos, no contra Alpine. El reviewer lo mira |
| El puente a `node` hace lento cada mutante de `dev_server.py` | La suite JS son tests puros, sin red ni ficheros: unos cientos de milisegundos. Si la campaña se dispara, se acota con `--workers` |
| `node` no está en la máquina de otro | R32 obliga a **fallar diciéndolo**. Un `skip` silencioso volvería a dejar el front sin comprobar |
| Base64 de `/api/split` infla la remesa un 33 % | Ya decidido y asumido en F-002 para el piloto; F-007 no lo cambia |
| El navegador se queda sin memoria con 22 PDFs | Los blobs se revocan al cambiar de parte (§4) |
| Alguien «arregla» el 503 de archivar tocando la puerta de entorno | Pantalla propia y texto explícito (§7) |

Alternativas descartadas, con motivo:

- **`Promise.all` sobre los 22 partes**: es literalmente lo que prohíbe el
  criterio 3.
- **Trocear la remesa en lotes de 3 con `Promise.all` por lote**: más simple
  de escribir, pero cada lote va al ritmo del parte más lento y deja plazas
  vacías. La cola con plazas las reutiliza en cuanto una queda libre.
- **Componer extracción y firma en una sola llamada al backend**: sumaría dos
  timeouts de 120 s bajo el corte de 230 s de la Function. Ya está decidido en
  `function_app.py` y no se rediscute.
- **Un `package.json` con Jest/Vitest**: dependencias, `node_modules` y una
  cadena de build en un front que a propósito no la tiene.

## 13 · Decisiones abiertas

| | Decisión | Recomendación | ¿Bloquea? |
|---|---|---|---|
| **D1** | **Cómo se trata `dev_server.py` frente a la puerta de cobertura** (§9) | **O1**: probarlo de verdad. Cierra a la vez el criterio 5 y el 6, no toca el arnés y no abre la puerta de las exclusiones. Si el humano quiere O2, es una feature de `arnes-base` | **No.** Con silencio se implementa O1 |
| **D2** | **El valor del límite de concurrencia** (§5) | **3 partes** (= 6 peticiones vivas). Los cinco argumentos están en §5. Es una constante de `js/config.js`: cambiarlo después es una línea | **No** |
| **D3** | **Qué confianza se envía al revalidar un campo corregido a mano** | **100**, marcando el campo como editado en pantalla. Si se mantuviera la confianza del modelo, corregir un campo no serviría de nada: el parte seguiría no apto para siempre. El coste es que el backend no distingue «lo leyó el modelo» de «lo escribió una persona»; registrar eso es trabajo de la persistencia, que hoy no existe (D4) | **No** |
| **D4** | **La remesa no se persiste**: si se recarga la pestaña, el trabajo se pierde (§10.1) | Aceptarlo en el piloto y **dar de alta una feature** en `harness/features.json` para los endpoints de persistencia del pipeline, en `postventa-api`. No se implementa aquí | **No**, pero el humano tiene que saberlo antes de enseñar el front a Posventa |
| **D5** | **Qué navegador se soporta** | Edge/Chrome. El selector de carpeta usa `webkitdirectory`, que Firefox no implementa igual. Es el navegador corporativo | **No** |
