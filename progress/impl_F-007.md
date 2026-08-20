<!-- progress/impl_F-007.md -->
# F-007 · Front de carga y revisión — Informe de implementación

> Rama `feature/F-007-front`. Rigor **`estandar`**: fase RED en los requisitos
> centrales (T2, T3, T4, T7, T8), cobertura de líneas cambiadas ≥ 80 % y
> campaña de mutación con supervivientes analizados. **No** se exige fase RED
> en todo ni cero supervivientes.
>
> **Ni un dato real.** Todos los códigos, nombres y textos de este informe y de
> los tests están **inventados**. Ningún parte de `muestras/` se ha copiado al
> repositorio ni se ha impreso en ninguna salida.

## Decisiones del humano aplicadas (2026-08-20)

Las cinco decisiones abiertas de `design.md` §13 quedaron resueltas por el
humano el **2026-08-20**, antes de implementar. Se aplican tal cual:

| | Decisión del humano (2026-08-20) | Dónde se materializa |
|---|---|---|
| **D1** | **`dev_server.py` se PRUEBA** (opción O1 de `design.md` §9). Nada de excluirlo de la puerta de cobertura ni de moverlo a una carpeta excluida: se le escriben tests. Cierra a la vez los criterios de aceptación 5 y 6, no toca el arnés genérico y es lo único que reproduce en local el proxy de la Static Web App | T3 (`tests/test_f007_dev_server.py`), resumido en el `README.md` del front |
| **D2** | **El límite de concurrencia es 3 partes** (= 6 peticiones vivas), como razona `design.md` §5 | T10 (`js/config.js`, `CONCURRENCIA_PARTES: 3`) |
| **D3** | **Un campo corregido a mano vale confianza 100 y se marca como editado.** Lo ha mirado y escrito una persona: es el dato más fiable que hay y el semáforo tiene que poder pasar a verde. La marca permite distinguir después lo que escribió la persona de lo que dijo la IA | T8 (`js/pipeline.js`), T10/T11 (marca en pantalla) |
| **D4** | **La remesa NO se persiste en esta feature.** Recargar la pestaña pierde el trabajo de revisión, y se acepta para el piloto. **No se resuelve por la vía fácil**: prohibido `localStorage` e `IndexedDB`, porque los partes llevan DNI y observaciones de clientes (R28–R30). La solución está dada de alta como **F-019 · Endpoints de persistencia**, que es del servicio `postventa-api`, no del front | Nada que implementar aquí; se cita en el `README.md` del front y en `design.md` §10 |
| **D5** | **Navegador soportado: Edge/Chrome** (el selector de carpeta usa `webkitdirectory`, que Firefox no implementa igual) | T10/T12 (`README.md` del front) |

---

## T1 · Recuperar el esqueleto del front — HECHA

El esqueleto no se ha reescrito: ya estaba verificado. El líder lo recuperó en
el commit `440700c` («F-007: recuperado el esqueleto del front, que el merge de
dev habia borrado»), porque el merge de `dev` sobre esta rama lo había borrado
—`dev` lo tiene eliminado, se sacó de F-001—.

Los seis ficheros de `design.md` §1 están en el árbol:

```
services/postventa-front/index.html
services/postventa-front/css/styles.css
services/postventa-front/js/config.js
services/postventa-front/js/app.js
services/postventa-front/dev_server.py
services/postventa-front/staticwebapp.config.json
```

### Fase RED de R31 — el guardián que ya existía muerde

`bash harness/init.sh` con el esqueleto en el árbol y el servicio **sin
declarar**. Salida real, sin recortar la parte que importa:

```
$ bash harness/init.sh
[OK] Arnés v1.5.2 (2026-08-18)
[OK] Python: Python 3.12.7
...
    19 features, 13 abiertas, en curso: ['F-007'], bloqueadas: ninguna
[OK] features.json válido
[OK] BACKLOG.md al día
    niveles: critico, documental, estandar; por defecto critico; umbral de cobertura 80%
[OK] harness/rigor.json y niveles declarados: válidos
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 56 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
..............F
================================== FAILURES ===================================
_____________ test_f001_r4_cada_servicio_en_disco_esta_declarado ______________
tests\test_servicios_declarados.py:39: in test_f001_r4_cada_servicio_en_disco_esta_declarado
    assert relativa in declaradas, f"{relativa} existe pero no está declarado"
E   AssertionError: services/postventa-front existe pero no está declarado
E   assert 'services/postventa-front' in {'services/postventa-api'}
=========================== short test summary info ===========================
FAILED tests/test_servicios_declarados.py::test_f001_r4_cada_servicio_en_disco_esta_declarado
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!
1 failed, 14 passed in 0.54s
[KO] pytest en rojo (¿pytest instalado en el venv?)
    1 servicio(s): api (python)
[OK] harness/servicios.json válido
[OK] servicio api (services/postventa-api): pytest en verde (caché: árbol sin cambios desde el último verde)
[KO] PUERTA COBERTURA: 0.0% de 114 líneas cambiadas cubiertas (0/114, umbral 80%, nivel estandar)
[OK] Rama actual: feature/F-007-front
----------------------------------------
2 comprobaciones fallidas. NO empieces a trabajar.
```

Eso es exactamente lo que demuestra el criterio de aceptación 5: **hasta hoy
nadie comprobaba el front**. El guardián existe desde F-001
(`tests/test_servicios_declarados.py`) y es la primera vez que puede morder,
porque hasta ahora la carpeta no estaba en el árbol.

**Los dos rojos son los esperados y ninguno más**:

1. `test_f001_r4_cada_servicio_en_disco_esta_declarado` → **fase RED de R31**,
   se cierra en T2.
2. `PUERTA COBERTURA: 0.0% de 114 líneas cambiadas cubiertas (0/114)` →
   **fase RED de R34**. Las 114 líneas son las de `dev_server.py`, que llega
   entero como fichero nuevo frente a `dev`. Es literalmente el problema que
   expulsó al front de F-001, y es lo que cierra T3 con D1/O1.

---

## T2 · El front entra en el arnés — HECHA

Tres ficheros:

- `harness/servicios.json`: se declara el servicio `front`
  (`ruta: services/postventa-front`, `lenguaje: python`, **sin `venv` y sin
  `comando_tests`**), con el porqué de las tres decisiones escrito en el
  `$doc` del fichero.
- `services/postventa-front/tests/conftest.py`: raíz del front en `sys.path`
  (para `import dev_server` sin instalar nada) y **guardia de red de sesión**
  (R33), calcada de la del backend.
- `services/postventa-front/tests/test_f007_declaracion.py`: cuatro tests de
  R31 —el servicio está declarado, apunta a esta carpeta, va como `python` y
  no declara `venv` ni `comando_tests`—.

Suite del front en verde:

```
$ cd services\postventa-front
$ python -m pytest -q
....                                                                     [100%]
4 passed in 0.02s
```

### Fase RED de R34 — la puerta de cobertura, que es el problema de fondo

`bash harness/init.sh` ya **no** falla por la declaración (el front aparece
como servicio y su suite se ejecuta), pero sigue en rojo por la puerta de
cobertura. Salida real:

```
$ bash harness/init.sh
...
[OK] pytest en verde (con medición de cobertura)
    2 servicio(s): api (python), front (python)
[OK] harness/servicios.json válido
[OK] servicio api (services/postventa-api): pytest en verde (caché: árbol sin cambios desde el último verde)
....                                                                     [100%]
4 passed in 0.03s
[OK] servicio front (services/postventa-front): pytest en verde
[KO] PUERTA COBERTURA: 0.0% de 114 líneas cambiadas cubiertas (0/114, umbral 80%, nivel estandar)
[OK] Rama actual: feature/F-007-front
----------------------------------------
1 comprobaciones fallidas. NO empieces a trabajar.
```

**Ese `0/114` es el problema que expulsó al front de F-001**, ahora medido y
con nombre. Son las líneas ejecutables de `dev_server.py`, que llega entero
como fichero nuevo frente a `dev`: `harness/alcance.py` mete en el alcance
cualquier `.py` que no lleve un segmento `tests`, `specs`, `progress` o `docs`
en su ruta, y no existe lista de exclusiones. **No hay opción «no tocarlo»**.
Se cierra en T3 escribiéndole tests (decisión **D1**, opción O1).

---

## T3 · `dev_server.py` probado de verdad — HECHA (cierra la RED de T2)

`services/postventa-front/tests/test_f007_dev_server.py`: **21 tests**, todos
con dobles y **ni un socket** (la guardia de sesión de T2 lo garantiza).

Qué se cubre, agrupado como pedía la tarea:

| Zona | Tests |
|---|---|
| Routing | `/api/*` va al proxy y **no** se sirve de disco; lo demás lo sirve `SimpleHTTPRequestHandler`; `POST` sobre estático → **405**; `OPTIONS` → 204 con CORS; tabla de rutas donde `/api` a secas y `/apiario.html` **no** son API (el prefijo es `/api/`) |
| Saneo de cabeceras | `host` y `connection` fuera; `DEV_FAKE_PRINCIPAL` dentro **solo si está declarado**; `Content-Length` no numérico no lee cuerpo |
| Respuesta | `transfer-encoding`, `connection` y `content-encoding` suprimidas; 204 sin cuerpo no escribe nada; `https://` usa `HTTPSConnection` |
| Errores | backend inalcanzable → **502 en JSON**; fallo al hablar → 502 en JSON y conexión cerrada; un `close()` roto se anota en debug y la respuesta se sirve igual |
| CLI y arranque | valores por defecto (5173 / 7073); `--port`, `--api` y `--root`; `Ctrl+C` apaga ordenadamente y devuelve 0; **sin `index.html` → código 1** y ni se construye el servidor |

Detalle que merece quedar escrito: el 502 se comprueba **en JSON**, no solo por
el código. El front clasifica una respuesta no-JSON como `desconocido` (R26); si
el proxy devolviera HTML aquí, el motivo real quedaría escondido detrás de un
«respuesta inesperada del servicio».

### La fase RED cerrada: antes y después

```
ANTES  (T2)  [KO] PUERTA COBERTURA: 0.0% de 114 líneas cambiadas cubiertas (0/114, umbral 80%, nivel estandar)
DESPUÉS (T3) [OK] PUERTA COBERTURA: 98.3% de 116 líneas cambiadas cubiertas (114/116, umbral 80%, nivel estandar)
```

Salida real del portero tras T3:

```
$ bash harness/init.sh
...
16 passed in 0.55s
[OK] pytest en verde (con medición de cobertura)
    2 servicio(s): api (python), front (python)
[OK] harness/servicios.json válido
[OK] servicio api (services/postventa-api): pytest en verde (caché: árbol sin cambios desde el último verde)
..............................                                           [100%]
30 passed in 0.20s
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: 98.3% de 116 líneas cambiadas cubiertas (114/116, umbral 80%, nivel estandar)
[OK] Rama actual: feature/F-007-front
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

Las **2 líneas de 116 que quedan sin cubrir** son, a propósito, las dos que solo
se ejecutan con un socket o con un proceso de verdad: `DevHandler.__init__`
(llama al `__init__` del handler de la biblioteca estándar, que exige un socket
aceptado) y el `sys.exit(main())` del `if __name__ == "__main__"`. Cubrirlas
exigiría levantar un servidor real, que es exactamente lo que R33 prohíbe.

**Criterio de aceptación 6 cerrado**: la decisión sobre `dev_server.py` frente a
la puerta de cobertura es **D1/O1 — probarlo**, está razonada en `design.md` §9
con las cinco opciones y sus motivos, y se resume en el `README.md` del front
(T12).

---

## T4 · La cola: el límite de concurrencia — HECHA

`tests_js/cola.test.js` **primero**, `js/cola.js` después, más el puente
`tests/test_f007_js.py`.

### Fase RED de R7–R12 (traza real)

Test escrito, módulo inexistente:

```
$ cd services\postventa-front
$ node --test "tests_js/*.test.js"
node:internal/modules/cjs/loader:1459
  throw err;
  ^

Error: Cannot find module '../js/cola.js'
Require stack:
- C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-front\tests_js\cola.test.js
    at Module._resolveFilename (node:internal/modules/cjs/loader:1456:15)
    at defaultResolveImpl (node:internal/modules/cjs/loader:1066:19)
    at resolveForCJSWithHooks (node:internal/modules/cjs/loader:1071:22)
    at Module._load (node:internal/modules/cjs/loader:1242:25)
    at wrapModuleLoad (node:internal/modules/cjs/loader:255:19)
    at Module.require (node:internal/modules/cjs/loader:1556:12)
    at require (node:internal/modules/helpers:152:16)
    at Object.<anonymous> (...\tests_js\cola.test.js:16:31)
    at Module._compile (node:internal/modules/cjs/loader:1812:14)
    at Object..js (node:internal/modules/cjs/loader:1943:10) {
  code: 'MODULE_NOT_FOUND',
  ...
}
```

### Verde tras escribir `js/cola.js`

```
$ node --test "tests_js/*.test.js"
✔ f007 R7: nunca hay más tareas vivas que el límite (8.3361ms)
✔ f007 R7: no arranca la siguiente hasta que una plaza queda libre (2.0237ms)
✔ f007 R7: un límite mayor que el número de tareas no rompe nada (1.5988ms)
✔ f007 R7: una lista vacía de tareas devuelve una lista vacía (0.2743ms)
✔ f007 R7: un límite menor que 1 es un error, no un «sin límite» silencioso (0.9555ms)
✔ f007 R9: alTerminar se llama exactamente una vez por tarea (0.3072ms)
✔ f007 R9: el progreso también avanza cuando un parte termina en error (0.2783ms)
✔ f007 R10: un error no para a los demás y viaja como resultado, no como excepción (0.2572ms)
✔ f007 R10: una tarea que lanza de forma síncrona tampoco tumba la cola (0.2693ms)
✔ f007 R10: los resultados salen en el orden de entrada aunque terminen desordenados (0.3648ms)
✔ f007 R11: reintentar un parte suelto pasa por la misma cola y el mismo límite (1.6876ms)
✔ f007 R12: una tarea que falla libera su plaza, no la deja ocupada para siempre (0.574ms)
✔ f007 R7: la cola no llama a una tarea más de una vez (0.381ms)
ℹ tests 13
ℹ pass 13
ℹ fail 0
```

Ni un reloj real: todas las promesas son diferidas que el test resuelve a mano.
Un test de concurrencia que dependa de tiempos falla en la máquina de otro.

### Desviación respecto a `tasks.md`: el argumento de `node --test`

`tasks.md` y `design.md` documentan `node --test tests_js`. **En Node 24 eso no
funciona**: un argumento que es un directorio se intenta cargar como módulo y
la ejecución muere con `MODULE_NOT_FOUND` antes de descubrir ningún test:

```
$ node --test tests_js
Error: Cannot find module 'C:\...\services\postventa-front\tests_js'
    code: 'MODULE_NOT_FOUND'
✖ tests_js (126.9105ms)
```

Se usa el **patrón** `node --test "tests_js/*.test.js"`, que lo expande el
propio Node y funciona igual en PowerShell y en Git Bash. Es un hecho del
entorno, no un cambio de diseño: el mecanismo, el alcance y el contrato de la
tarea son los mismos. Queda documentado en el puente, en el `README.md` del
front y aquí.

### El puente (R32)

`tests/test_f007_js.py`, tres tests:

- `node` está en el PATH — y **si no está, la suite FALLA diciéndolo**, no se
  salta con un `skip`. Un `skip` silencioso volvería a dejar el front sin
  comprobar, que es el agujero que cierra F-007.
- `node --test tests_js/*.test.js` termina en 0; si no, la aserción **propaga
  la salida entera** de Node, para que el motivo se lea sin volver a lanzarlo.
- hay al menos un `*.test.js`: un patrón sin coincidencias no es un error para
  Node, y sería un verde que no significa nada.

```
$ cd services\postventa-front
$ python -m pytest -q
.................................                                        [100%]
33 passed in 0.37s
```

---

## T5 · `js/traza.js`: el único registro permitido — HECHA

R28. `traza({hash, paso, estado, http}, salida)` se queda con **cuatro claves**
y tira el resto. Es un **filtro**, no una convención: aunque alguien le pase el
parte entero por descuido, el DNI y las observaciones no salen.

Dos decisiones que van más allá de la letra del requisito, y por qué:

- **Solo primitivos.** Un filtro por claves no vería un dato personal escondido
  dentro de un objeto anidado bajo una clave permitida
  (`estado: {campo: "dni_cliente", valor: "..."}`). Se descarta cualquier valor
  que no sea `string`, `number` o `boolean`.
- **La salida es inyectable** (`console.info` por defecto). Así se prueba el
  camino real sin ensuciar la salida de la suite, y `console` no se llama desde
  ningún otro módulo del front: si el registro pasa por un solo sitio, basta con
  vigilar ese sitio.

`tests_js/traza.test.js`: 9 tests. Los valores personales de los tests están
**inventados** (`00000000T`, «Inventado: el cliente no estaba en casa») y se
usan justo para comprobar que el filtro los tira: se serializa la salida y se
afirma que **no contiene** ninguno de los dos.

```
$ node --test "tests_js/*.test.js"
✔ f007 R28: solo salen hash, paso, estado y http (1.8785ms)
✔ f007 R28: las claves permitidas son exactamente cuatro (0.1787ms)
✔ f007 R28: un DNI o unas observaciones que se cuelen se descartan (0.3377ms)
✔ f007 R28: un objeto anidado bajo una clave permitida tampoco pasa (0.1986ms)
✔ f007 R28: las claves ausentes no se inventan (0.2578ms)
✔ f007 R28: un evento que no es un objeto no revienta ni escribe basura (0.1815ms)
✔ f007 R28: traza devuelve lo saneado, para que se pueda afirmar (0.2794ms)
✔ f007 R28: el objeto original no se modifica (0.185ms)
✔ f007 R28: sin salida inyectada escribe por consola, y solo lo saneado (0.2643ms)
ℹ tests 22
ℹ pass 22
ℹ fail 0
```

---

## T6 · `js/seleccion.js`: qué entra en la remesa y cómo se envía — HECHA

R1–R4. Lógica pura: recibe un array de `File` (o cualquier cosa con `name` y
`size`) y no toca el DOM, que es lo que la hace probable sin navegador.

- `filtrarAdmitidos(ficheros)` → `{admitidos, descartados, mensajeDescartes}`.
  Los descartes traen **nombre y motivo**, y el mensaje dice **cuántos** (R2).
- `motivoDeRechazo(resultado)` devuelve **texto**, no un booleano: quien llama
  no tiene que inventarse el mensaje, y R3 exige explicar qué formatos se
  admiten.
- `formatearTamano(bytes)` para listar nombre y tamaño (R1).
- `formDataDeRemesa(ficheros)` con **un nombre de campo por índice**
  (`fichero_0`, `fichero_1`, …), no por nombre de fichero.

El test que justifica R4 por sí solo: **dos ficheros que se llaman igual**
—dos carpetas distintas con la misma remesa— siguen ocupando campos distintos.
Con el mismo nombre de campo, el backend (`req.files.values()`, un valor por
clave) perdería uno en silencio y una remesa de 3 PDFs entraría como 1.

Y `formDataDeRemesa([])` **lanza**: sin ficheros admitidos no se llega a
construir el cuerpo del `POST`, así que R3 se cumple por construcción, no por
buena voluntad de `app.js`.

```
$ node --test "tests_js/seleccion.test.js"
✔ f007 R1: una selección de PDFs y ZIPs se acepta entera (2.5946ms)
✔ f007 R1: cada fichero se puede listar con su nombre y su tamaño (0.2995ms)
✔ f007 R2: de una carpeta solo se queda lo que el backend sabe trocear (0.4424ms)
✔ f007 R2: se dice cuántos ficheros se han descartado y por qué (0.4362ms)
✔ f007 R2: la extensión se reconoce sin importar mayúsculas (0.2617ms)
✔ f007 R2: un nombre con puntos no engaña al filtro (0.1279ms)
✔ f007 R3: una selección sin PDF ni ZIP se rechaza y explica qué se admite (0.2684ms)
✔ f007 R3: una selección vacía también se rechaza en el navegador (0.2326ms)
✔ f007 R3: sin ficheros admitidos no se puede ni construir el cuerpo del POST (0.5747ms)
✔ f007 R4: cada fichero viaja con un nombre de campo distinto (21.8323ms)
✔ f007 R4: dos ficheros que se llaman IGUAL no comparten nombre de campo (0.3776ms)
✔ f007 R4: el nombre original del fichero llega al backend (0.2239ms)
✔ f007 R4: una remesa de 22 partes son 22 campos distintos (0.5122ms)
✔ f007 R4: el FormData es inyectable, para no depender del entorno (0.195ms)
ℹ tests 14
ℹ pass 14
ℹ fail 0
```

---

## T7 · `js/api.js`: el cliente HTTP — HECHA

R12 y R23–R27. `tests_js/api.test.js` **primero**, módulo después.

### Fase RED (traza real)

```
$ cd services\postventa-front
$ node --test "tests_js/api.test.js"
node:internal/modules/cjs/loader:1459
  throw err;
  ^

Error: Cannot find module '../js/api.js'
Require stack:
- C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-front\tests_js\api.test.js
    at Module._resolveFilename (node:internal/modules/cjs/loader:1456:15)
    at defaultResolveImpl (node:internal/modules/cjs/loader:1066:19)
    at resolveForCJSWithHooks (node:internal/modules/cjs/loader:1071:22)
    at Module._load (node:internal/modules/cjs/loader:1242:25)
    at wrapModuleLoad (node:internal/modules/cjs/loader:255:19)
    at Module.require (node:internal/modules/cjs/loader:1556:12)
    at require (node:internal/modules/helpers:152:16)
    at Object.<anonymous> (...\tests_js\api.test.js:11:32)
    at Module._compile (node:internal/modules/cjs/loader:1812:14)
    at Object..js (node:internal/modules/cjs/loader:1943:10) {
  code: 'MODULE_NOT_FOUND',
  ...
}
```

### Verde tras escribir `js/api.js`

```
$ node --test "tests_js/api.test.js"
✔ f007 R27: la pantalla consulta GET /api/health al cargar (2.5588ms)
✔ f007 R27: los seis endpoints cuelgan de baseApi (0.3468ms)
✔ f007 R23: un 502 se reintenta 2 veces con esperas de 1 s y 3 s (1.0677ms)
✔ f007 R23: un fallo de conexión también se reintenta (0.3597ms)
✔ f007 R23: si el reintento va bien, el usuario no ve ningún error (0.2504ms)
✔ f007 R24: un 400 no se reintenta y muestra el error del backend (0.2781ms)
✔ f007 R24: un 413 no se reintenta y sale como error de petición (0.2593ms)
✔ f007 R24: un 409 sale como no_apto y no se reintenta (18.972ms)
✔ f007 R24: sin campo `error`, el mensaje no queda vacío (0.5078ms)
✔ f007 R25: un 503 en archivar dice que este entorno no archiva y no reintenta (0.5171ms)
✔ f007 R26: una respuesta HTML sale como desconocido con su código HTTP (0.3178ms)
✔ f007 R26: un error 500 con cuerpo HTML tampoco lanza excepción sin capturar (0.2045ms)
✔ f007 R26: un cuerpo vacío en un 200 también es respuesta inesperada (0.1693ms)
✔ f007 R12: cada petición se programa para abortar a los 180 s (0.1205ms)
✔ f007 R12: la señal de aborto viaja en la petición (0.0948ms)
✔ f007 R12: al dispararse el timeout, la petición se aborta y es transitoria (7.3561ms)
✔ f007 R8: extraer y firma envían el fichero y el hash del parte (2.25ms)
✔ f007 R8: firma usa su propio endpoint (0.2442ms)
✔ f007 R17: validar va en JSON y no toca extraer ni firma (0.1788ms)
✔ f007 R4: trocear envía el multipart de la remesa tal cual (0.1918ms)
✔ f007 R26: el multipart NO lleva Content-Type puesto a mano (0.143ms)
✔ f007 R28: la traza del cliente lleva solo hash, paso, estado y http (0.3601ms)
✔ f007 R28: la traza de un error tampoco lleva el cuerpo de la respuesta (0.1556ms)
ℹ tests 23
ℹ pass 23
ℹ fail 0
```

### Decisiones de diseño que conviene no deshacer

- **Una sola forma de error**: `ErrorApi {tipo, http, mensaje, avisos}` con
  `tipo ∈ {transitorio, peticion, no_apto, entorno, desconocido}`. `clasificar`
  es una función **pura** y por eso se prueba código a código.
- **Solo se reintenta lo `transitorio`** (502, fallo de red, aborto por
  timeout). Un 400 no mejora repitiéndolo y un 503 de archivar es la **puerta
  de entorno**: insistir no la ablanda.
- **El 503 tiene texto propio**: «Este entorno no archiva… No es un fallo y no
  hay nada que arreglar aquí». Pintarlo como error rojo genérico es lo que
  llevaría a alguien a «arreglarlo» tocando `ARCHIVO_HABILITADO`, que es
  exactamente lo que no puede pasar.
- **Códigos no contemplados (500, 404…)**: `desconocido` y **sin reintento**.
  No hay razón para creer que mejoren y se enseñan tal cual en vez de
  esconderlos.
- **El multipart NO lleva `Content-Type` puesto a mano**: ponerlo rompe el
  `boundary` que genera el navegador y el backend recibe un cuerpo que no sabe
  parsear. Hay un test que lo vigila.
- **`fetch`, `esperar` y `programarTimeout` se inyectan.** El backoff de R23
  se prueba en milisegundos y **ni un test abre red**.
