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

---

## T8 · `js/pipeline.js`: la orquestación de un parte — HECHA

R8, R13–R22 y R29. `tests_js/pipeline.test.js` **primero**, módulo después.

### Fase RED (traza real)

```
$ cd services\postventa-front
$ node --test "tests_js/pipeline.test.js"
node:internal/modules/cjs/loader:1459
  throw err;
  ^

Error: Cannot find module '../js/pipeline.js'
Require stack:
- C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-front\tests_js\pipeline.test.js
    at Module._resolveFilename (node:internal/modules/cjs/loader:1456:15)
    at defaultResolveImpl (node:internal/modules/cjs/loader:1066:19)
    at resolveForCJSWithHooks (node:internal/modules/cjs/loader:1071:22)
    at Module._load (node:internal/modules/cjs/loader:1242:25)
    at wrapModuleLoad (node:internal/modules/cjs/loader:255:19)
    at Module.require (node:internal/modules/cjs/loader:1556:12)
    at require (node:internal/modules/helpers:152:16)
    at Object.<anonymous> (...\tests_js\pipeline.test.js:23:5)
    at Module._compile (node:internal/modules/cjs/loader:1812:14)
    at Object..js (node:internal/modules/cjs/loader:1943:10) {
  code: 'MODULE_NOT_FOUND',
  ...
}
```

Un segundo rojo, ya con el módulo escrito, que merece constar porque **el fallo
era del test, no del código**: `assert.equal(fichero.size, 5)` sobre
`"JVBERg=="`, que son los **cuatro** bytes de `%PDF`.

```
✖ f007 R14: el PDF del parte se reconstruye desde contenido_b64 (1.273ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  4 !== 5
      at TestContext.<anonymous> (...\tests_js\pipeline.test.js:455:10)
```

Corregida la expectativa (4 bytes), no el módulo.

### Verde

```
$ node --test "tests_js/pipeline.test.js"
✔ f007 R8: extraer y firma se piden EN PARALELO (9.4194ms)
✔ f007 R8: validar NO se pide hasta que las dos han respondido (0.8664ms)
✔ f007 R8: el cuerpo de validar son las DOS respuestas verbatim (0.3632ms)
✔ f007 R8: un fallo de extraer se propaga y no se valida a medias (0.7773ms)
✔ f007 R18: el cuerpo de validar lleva SIEMPRE las nueve claves (0.1922ms)
✔ f007 R18: un campo vacío viaja como valor null, no como cadena vacía (0.1816ms)
✔ f007 R18: las nueve claves son las del dominio, ni una más (0.1253ms)
✔ f007 R16: un campo corregido a mano viaja con confianza 100 (D3) (0.1289ms)
✔ f007 R16: el campo corregido queda MARCADO como editado (D3) (0.1762ms)
✔ f007 R16: corregir un campo no toca el resto del cuerpo ni la traza (0.2306ms)
✔ f007 R15: se destacan los campos por debajo del umbral del dominio (0.1857ms)
✔ f007 R15: un campo corregido a mano deja de ser dudoso (0.1421ms)
✔ f007 R17: revalidar llama SOLO a validar (0.3074ms)
✔ f007 R17: revalidar sin extracción previa es un error de programación (0.3195ms)
✔ f007 R13: el semáforo sale de veredicto y destino, no de una escala nueva (0.1232ms)
✔ f007 R13: sin veredicto todavía, no hay semáforo que pintar (0.0903ms)
✔ f007 R13: un apto con destino que no es archivo_y_cierre NO es verde (0.0599ms)
✔ f007 R21: solo es archivable apto + archivo_y_cierre (0.0923ms)
✔ f007 R21: componer el cuerpo de archivo de un parte no apto es imposible (0.2774ms)
✔ f007 R21: un parte ya archivado no se vuelve a componer (0.2065ms)
✔ f007 R20: el cuerpo de archivar lleva el fichero y los cinco campos (21.3853ms)
✔ f007 R29: al archivar NO viajan ni el DNI ni las observaciones (0.4195ms)
✔ f007 R20: el cuerpo de archivo usa el valor CORREGIDO del código de obra (0.1565ms)
✔ f007 R14: el PDF del parte se reconstruye desde contenido_b64 (0.3128ms)
✔ f007 R14: sin contenido_b64 no se inventa un PDF vacío (0.1956ms)
ℹ tests 25
ℹ pass 25
ℹ fail 0
```

### Los contratos del backend, verificados contra el código real (sin tocarlo)

Antes de escribir el módulo se leyeron los handlers para no inventarse nada:

- Los **nueve campos** y su orden salen de
  `domain/models/extraccion.py::CAMPOS_DEL_PARTE`: `promocion`, `codigo_obra`,
  `unidad`, `numero_incidencia`, `fecha_servicio`, `descripcion`,
  `dni_cliente`, `observaciones`, `numero_pagina`. Hay un test que fija esa
  lista: si el dominio cambia, el front se entera por un rojo y no por un 400
  en producción.
- Los **cinco campos de archivo** salen de
  `interface_adapters/api/archivar.py::CAMPOS_OBLIGATORIOS`.
- Los valores de `veredicto` y `destino`, de
  `domain/models/validacion.py` (`Veredicto`, `Destino`).
- El **umbral 50** de R15, de `domain/models/firma.py::UMBRAL_CONFIANZA`.

**No se ha modificado ni un fichero de `services/postventa-api/`.**

### D3 aplicada, y por qué el «editado» importa

`aplicarEdiciones` marca el campo corregido con `editado: true` y
`confianza_pct: 100`. El efecto que se ve en pantalla lo prueba un test
explícito: **un campo corregido a mano deja de aparecer entre los dudosos**, o
sea, corregirlo sirve para algo y el semáforo puede pasar a verde. Si se
mantuviera la confianza del modelo, el parte seguiría no apto para siempre.

La extracción original **no se muta**: se conserva íntegra para poder volver a
ella, y hay un test que lo comprueba.

### R21, defendido por construcción

`cuerpoDeArchivo` **lanza** si el parte no es apto o si ya está archivado. No
basta con no pintar el botón: aunque el usuario lo pulse dos veces, la petición
no se llega a componer.

---

## T9 · `tests/test_f007_estaticos.py`: el contrato de los ficheros estáticos — HECHA

Un front sin cadena de build no tiene compilador que avise: si alguien añade un
`defer` «para que cargue antes», la pantalla queda muerta y el fallo solo se ve
abriendo el navegador. Este fichero es ese compilador. 9 tests:

- Los scripts **propios** van al final del `<body>`, **sin `defer`** y sin
  `type="module"` (un módulo se difiere de forma implícita: el mismo fallo por
  otra puerta).
- **Alpine** va una vez, **con `defer`**, en el `<head>` y con la **versión
  fija 3.14.1**.
- Los scripts propios van **en orden de dependencia** y `app.js` es **el
  último**: es el pegamento y necesita a los demás cargados. La lista canónica
  (`ORDEN_CANONICO`) es la de los siete de T10, así que la guardia ya vigila lo
  que llega en la tarea siguiente.
- Un script propio **no declarado** en esa lista también es un problema: nadie
  añade un `js/loquesea.js` sin pasar por aquí.
- `baseApi: "/api"`, proxy del `dev_server` en **7073**, y el marcador
  `<TENANT_ID>` **sin resolver** (además de un barrido de GUIDs sobre el
  fichero entero, por si alguien lo pone en otro sitio).

### Fase RED de la propia guardia (traza real, copia rota FUERA del árbol)

La comprobación es una **función pura sobre el texto**
(`problemas_del_index(html)`), lo que permite demostrarla. Se copió el
`index.html` real al directorio temporal de la sesión —**fuera del
repositorio**—, se le añadió `defer` y se ejecutó la misma aserción:

```
$ sed 's|<script src="js/app.js"></script>|<script defer src="js/app.js"></script>|' index.html > %TEMP%\...\index_roto.html
$ python -m pytest %TEMP%\...\test_red_t9.py -q
F                                                                        [100%]
================================== FAILURES ===================================
_____________ test_f007_r36_el_index_cumple_el_contrato_de_carga ______________

    def test_f007_r36_el_index_cumple_el_contrato_de_carga():
        problemas = problemas_del_index(ROTO.read_text(encoding="utf-8"))
>       assert problemas == [], "\n".join(problemas)
E       AssertionError: js/app.js lleva defer: Alpine arrancaría antes de que exista appPostventa y la pantalla quedaría muerta
E       assert ['js/app.js l...daría muerta'] == []
E
E         Left contains one more item: 'js/app.js lleva defer: Alpine arrancaría antes de que exista appPostventa y la pantalla quedaría muerta'
E         Use -v to get more diff

...\scratchpad\test_red_t9.py:13: AssertionError
=========================== short test summary info ===========================
FAILED ...\scratchpad\test_red_t9.py::test_f007_r36_el_index_cumple_el_contrato_de_carga
1 failed in 1.02s
```

Ni el HTML roto ni ese test temporal se han versionado. Lo que **sí** queda en
el repositorio es el mismo destrozo hecho **en memoria**: tres tests
(`la guardia caza un index estropeado` con `defer` y con `type=module`, y
`la guardia caza los scripts desordenados`) construyen la copia rota a partir
del `index.html` real y comprueban que la guardia la caza. Sin ellos,
`problemas_del_index` podría estar devolviendo siempre lista vacía y nadie se
enteraría.

```
$ python -m pytest tests/test_f007_estaticos.py -q
.........                                                                [100%]
9 passed in 0.03s
```

---

## T10 · `index.html` y `js/config.js`: la pantalla — HECHA

`index.html` pasa de «Estado del servicio» a la pantalla real:

- **Zona de carga** con `drop`, selector de ficheros y selector de **carpeta**
  (`webkitdirectory`, Edge/Chrome, **D5**), la lista de lo seleccionado con
  nombre y tamaño y el aviso de descartes. **Nada se envía hasta confirmar.**
- **Progreso «N de M partes terminados»** con barra, para las tres fases largas.
- **Lista de partes** con semáforo (verde / ámbar / rojo), `hash` corto, origen,
  páginas de origen, los motivos del veredicto y, si falló, su error con un
  enlace para **reintentarlo él solo**.
- **Panel de detalle**: los nueve campos editables con su confianza, con los
  dudosos (< 50) destacados en ámbar y la marca **editado** en verde (**D3**),
  la clasificación de la firma, el botón de **revalidar** y el **PDF del parte**
  en un `<iframe>` sobre un blob.
- **Archivo** con **confirmación explícita** en dos pasos, y **pantalla propia
  para el 503** —en azul, no en rojo—: es la puerta de entorno de F-006 y
  pintarla como fallo llevaría a alguien a «arreglarla».
- El pie recuerda lo de **D4**: el trabajo de revisión vive en esta pestaña y
  recargar lo pierde, hasta que llegue **F-019**.

Los **siete scripts propios** van al final del `<body>`, **sin `defer`**, en
orden de dependencia: `config`, `traza`, `cola`, `api`, `seleccion`,
`pipeline`, `app`. Alpine sigue con `defer`, en el `<head>` y con `3.14.1`.

`js/config.js` declara, con el porqué al lado de cada número:
`CONCURRENCIA_PARTES: 3` (**D2**), `TIMEOUT_PETICION_MS: 180000`,
`REINTENTOS: 2`, `ESPERAS_MS: [1000, 3000]` y `UMBRAL_CONFIANZA: 50`.
`baseApi` no se toca.

### Cuatro guardias nuevas en `tests/test_f007_estaticos.py`

- **están los siete scripts propios**, exactamente en el orden canónico;
- `CONCURRENCIA_PARTES` vale **3** y vive en `config.js` (R7/D2);
- timeout, reintentos, esperas y umbral están declarados (R12);
- **D4 vigilada por un test**: ni `localStorage`, ni `sessionStorage`, ni
  `indexedDB`, ni `document.cookie` en ningún `js/*.js` ni en el `index.html`.
  Es la vía fácil que **no** se puede tomar: los partes llevan DNI y
  observaciones (R28). El test mira las líneas de **código**, no los
  comentarios, porque la prohibición se explica por escrito en varios sitios.

Un rojo intermedio que merece constar, porque lo cazó **la guardia de la
guardia** de T9: al crecer el `index.html`, el test que comprueba que se detecta
el desorden de scripts se apoyaba en que `config.js` y `app.js` estuvieran
pegados, y dejó de destrozar nada:

```
✗ test_f007_r36_la_guardia_caza_los_scripts_desordenados
E       AssertionError: la sustitución no ha cambiado nada: revisa el index
```

Se reescribió para mover la etiqueta de `app.js` delante de la de `config.js`
sin suponer adyacencia. Es exactamente para lo que estaba puesta esa aserción.

```
$ bash harness/init.sh
...
49 passed in 0.73s
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: 98.3% de 116 líneas cambiadas cubiertas (114/116, umbral 80%, nivel estandar)
[OK] Rama actual: feature/F-007-front
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

---

## T11 · `js/app.js`: el pegamento de Alpine — HECHA

`app.js` pasa de comprobar `/health` a ser el estado de la pantalla: selección,
arranque de la cola, progreso, parte abierto, edición, revalidación,
confirmación y archivo, y revocado del blob al cambiar de parte.

**Sin lógica propia.** Todo lo que decide algo llama a los módulos de T4–T8:
`Seleccion.filtrarAdmitidos`, `Seleccion.formDataDeRemesa`,
`Cola.ejecutarConLimite`, `Api.*`, `Pipeline.procesarParte`,
`Pipeline.revalidar`, `Pipeline.semaforoDe`, `Pipeline.esArchivable`,
`Pipeline.cuerpoDeArchivo`, `Pipeline.ficheroDeParte`.

Detalles que se ven en el código y conviene no perder:

- **La misma cola para procesar y para archivar** (`_porLaCola`): otra fase,
  mismo límite. Es literalmente la misma función.
- **Reintentar un parte** vuelve a pasar por `_porLaCola` con una sola tarea
  (R11), no por un camino paralelo.
- **El blob se revoca** al abrir otro parte y al cerrar (`_revocarPdf`): 22
  blobs vivos es memoria que no vuelve.
- **El 503 no ensucia el parte**: se guarda en `entornoNoArchiva` y se pinta en
  su recuadro azul (R25).
- **Un 400 de `/api/split` vuelve al estado inicial** sin dejar filas a medias
  (R6).

### La revisión de T11, convertida en dos tests en vez de en una promesa

La verificación de la tarea pedía «revisar que `app.js` no contiene bucles de
reintento, ni cálculo de veredicto, ni composición de cuerpos». Una revisión no
se vuelve a ejecutar sola, así que se ha escrito como guardia:

- `test_f007_r36_app_js_es_solo_pegamento`: `app.js` no puede contener
  `new FormData`, `fetch(`, `setTimeout`, `archivo_y_cierre`, `console.` ni
  `JSON.stringify`. Cada prohibición lleva escrito **de qué módulo es** esa
  responsabilidad. `app.js` es la única habitación sin tests de la casa: esto
  impide que la lógica se mude ahí.
- `test_f007_r36_app_js_usa_los_modulos_probados`: y que efectivamente los use.

Y como `app.js` no lo ejecuta ningún test, se añadió al puente
`test_f007_r32_todos_los_modulos_del_front_compilan`: **`node --check` sobre
cada `js/*.js`**. Un paréntesis mal cerrado en `app.js` no lo cazaría nada hasta
abrir el navegador; ahora lo caza el portero.

```
$ bash harness/init.sh
...
52 passed in 1.07s
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: 98.3% de 116 líneas cambiadas cubiertas (114/116, umbral 80%, nivel estandar)
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

---

## T12 · `README.md` y las dos guardias documentales — HECHA

`services/postventa-front/README.md`: cómo se arranca (las dos terminales, en
líneas cortas para PowerShell), cómo se prueba, cómo está organizado y **por qué
se puede probar sin navegador**, las tres decisiones del `index.html`, el
resumen de la decisión **D1** con las cuatro opciones descartadas y su motivo, y
una sección **«Lo que este front NO hace (a propósito)»** con D4/F-019, F-010,
F-008/F-009 y el 503 de archivar.

### `tests/test_f007_documentacion.py` (R35), 8 tests

No juzgan la prosa; comprueban que el README **nombra la decisión, las opciones
descartadas y su motivo**: que dice literalmente que `dev_server.py` **se
prueba**, que cita `harness/alcance.py` (el motivo mecánico, que es el que
zanja la discusión) y **F-001** (el precedente), que recoge O2, O3, O4 y O5, que
menciona **F-019** y que `localStorage` está **prohibido**, que nombra
`webkitdirectory` (D5), y que explica cómo arrancar y cómo probar. Más uno que
comprueba que la decisión sigue también en `design.md` §9, porque R35 pide las
dos.

### `tests/test_f007_sin_datos_reales.py` (R30), 4 tests

Barre **todo el árbol del front**:

1. **Ningún binario de parte**: `.pdf`, `.zip`, `.jpg`, `.png`, `.tif`.
2. **Ningún DNI que no sea evidentemente inventado.** Convención explícita de
   la suite: un DNI de ejemplo tiene los **ocho dígitos iguales** (`00000000T`,
   `11111111H`). Cualquier otro `8 dígitos + letra` falla **diciendo el fichero
   y la línea**.
3. **Ninguna tirada larga de base64**, que es la forma en que un PDF real se
   colaría dentro de un fichero de texto.
4. Un test de la propia guardia, para que no pueda estar mirando al vacío.

El barrido **mordió al escribirlo**, que es la mejor prueba de que sirve:

```
E       AssertionError: posibles DNI reales en el repositorio:
        ['js/traza.js:26 (12…Z)', 'tests/test_f007_sin_datos_reales.py:121 (12…Z)'].
        Un DNI de ejemplo tiene los ocho dígitos iguales (00000000T)
```

Los dos eran ejemplos ilustrativos, no datos de nadie: el comentario de
`traza.js` pasó a `00000000T`, y el DNI del auto-test se compone en trozos
(`"1234" + "5678" + "Z"`) con el porqué escrito al lado —de una pieza, el
barrido marcaría su propio fichero—.

```
$ python -m pytest -q
..................................................................       [100%]
66 passed in 1.21s
```

---

## T13 · `dev_front.ps1` — HECHA

Envoltorio de una línea sobre `dev_server.py`, con `-Puerto` (5173), `-Api`
(`http://localhost:7073`) y `-Ayuda`. **UTF-8 con BOM y CRLF**, como manda
`docs/CONVENTIONS.md` para PowerShell.

### Desviación respecto a `tasks.md`: `-Ayuda` en lugar de `-?`

La verificación de la tarea era
`powershell -File services\postventa-front\dev_front.ps1 -?` → «imprime la
ayuda sin arrancar nada». **La segunda mitad se cumple; la primera no puede.**
Comprobado en esta máquina (Windows PowerShell 5.1):

```
> & powershell -NoProfile -File ...\dev_front.ps1 -? | Out-String
EXIT=0
LEN=0
```

Con `-File`, PowerShell 5.1 se queda el `-?`: **no ejecuta el script** —que es
la propiedad importante: no arranca nada— pero **tampoco imprime nada**. Y no es
cosa de este script: se reprodujo con tres scripts mínimos en el directorio
temporal, con y sin `[CmdletBinding()]`.

La segunda vía, `Get-Help`, tampoco servía **por la propia convención del
repositorio**: PowerShell solo indexa la ayuda basada en comentarios
(`<# .SYNOPSIS #>`) si el bloque es **lo primero del fichero**, y
`docs/CONVENTIONS.md` exige abrir cada fichero de código con un comentario con
su ruta relativa. Aislado con cinco variantes en el temporal:

```
=== a (<# .SYNOPSIS #> el primero, SIN comentario de ruta) ===   ayuda completa
=== b (# ruta/b.ps1 delante) ===                                 solo la sintaxis
=== c (# ruta/c.ps1 + CmdletBinding) ===                         solo la sintaxis
=== d (<# ruta/d.ps1 en la misma línea del <# ) ===              solo la sintaxis
=== e (ruta dentro del bloque, antes de .SYNOPSIS) ===           solo la sintaxis
```

**Solución: un `-Ayuda` explícito**, que funciona con `-File` y respeta las dos
cosas. Salida real:

```
> & powershell -NoProfile -File ...\dev_front.ps1 -Ayuda
dev_front.ps1 - front de Posventa en local

  USO
    .\dev_front.ps1 [-Puerto <int>] [-Api <url>] [-Ayuda]

  PARAMETROS
    -Puerto   Puerto del front. Por defecto 5173.
    -Api      Backend al que se proxian las rutas /api/*.
              Por defecto http://localhost:7073.
    -Ayuda    Imprime esta ayuda y NO arranca nada.

  ANTES, en otra terminal:
    cd ..\postventa-api
    func start --port 7073

  El 7073 no es el puerto por defecto de func: es el que espera el proxy.

EXIT=0
```

El porqué queda escrito en el propio script y en el `README.md`, para que nadie
«arregle» esto volviendo a `-?`.

### `tests/test_f007_dev_front_ps1.py`, 4 tests

Fichero **no previsto en `design.md` §2.1** y añadido a conciencia:
`dev_front.ps1` es la única pieza de F-007 que ejecuta una persona a mano, y la
que se usa en T14. Si estuviera roto, lo descubriría el humano en mitad de la
demo. Comprueba:

- **UTF-8 con BOM y solo CRLF** (sin BOM, PowerShell 5.1 lee mal las tildes);
- los tres parámetros con sus valores por defecto;
- que no lleva secretos, ni `TENANT`, ni la carpeta de nadie;
- que **`-Ayuda` imprime el uso, sale con 0 y no anuncia ningún servidor
  sirviendo**. Si `powershell` no está en el PATH, **falla diciéndolo**, igual
  que con `node` (R32).

---

## T14 · Verificación MANUAL (humano) — PENDIENTE

**No la puede firmar un agente**: hace falta abrir el navegador y soltar un
parte de verdad. Queda **pendiente del humano** y es la única casilla de F-007
que no está cerrada por la máquina.

**Terminal A** (backend; una línea por línea, sin `&&`):

```
cd C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api
func start --port 7073
```

*(Si no existe `local.settings.json`, copiarlo antes de
`local.settings.json.example` y rellenarlo. El **7073** no es el puerto por
defecto de `func`: es el que espera el proxy.)*

**Terminal B** (front):

```
cd C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-front
.\dev_front.ps1
```

Los diez puntos, con el **resultado real** de la ejecución del humano del
2026-08-20. Veredicto suyo, literal: **«funciona a la perfección»**.

| | Qué hay que ver | Resultado |
|---|---|---|
| 1 | `http://localhost:5173/` abre y el semáforo de servicio sale verde (`/api/health` por el proxy) | **OK** — `health` responde 200 |
| 2 | Al soltar un PDF de remesa, sale el número de partes y la lista | **OK** — `split` responde 200 (7,2 MB de entrada) y la lista se pinta |
| 3 | En **DevTools → Red**, procesando la remesa, **nunca más de 6 peticiones a `/api/` en vuelo** (3 partes × 2 llamadas) | **OK** — ver abajo |
| 4 | El progreso llega a «M de M» y ningún parte se queda colgado | **OK** — todas las peticiones en 200, ninguna colgada ni fallida |
| 5 | Al abrir un parte se ve su PDF y sus campos con la confianza | **OK** |
| 6 | Corregir un campo y revalidar cambia el veredicto **sin** llamar a `/api/extraer` ni a `/api/firma` | **OK** — ver abajo |
| 7 | Archivar responde **503 «este entorno no archiva»** | **OK** — «archivar correcto» |
| 8 | En la consola del navegador **no aparece** ningún DNI ni ninguna observación (R28) | **OK** — ver abajo |
| 9 | **R19** · el primer clic en archivar **no dispara**: pide confirmación, y solo el segundo actúa | **OK** |
| 10 | **R22** · la respuesta de archivar se pinta en el resumen | **OK** |

### La evidencia de los tres puntos que solo se ven en DevTools

**Punto 3 · la concurrencia.** Captura de la pestaña Red aportada por el humano
(no se versiona). La cascada muestra **tandas escalonadas de unas seis barras
solapadas**, con huecos entre grupos, en vez de las 44 llamadas de la remesa
disparadas a la vez. El patrón por parte es el esperado —`extraer` y `firma` en
paralelo, y `validar` después—, todas en **200**. Es la comprobación **visual**
que pedía el criterio de aceptación 3, y la que une los tests de `js/cola.js`
con el navegador real. Precisión honesta: es una **lectura de la cascada**, no
un recuento instante a instante; lo que descarta es justo lo que preocupaba,
que una remesa larga dispare N peticiones simultáneas.

**Punto 6 · revalidar no reprocesa.** Traza real de la consola al revalidar un
campo corregido:

```
{hash: 'e2cd481b…', paso: 'validar', estado: 'ok', http: 200}
```

**Un solo registro, y su paso es `validar`.** Si el front hubiera reprocesado,
al lado habría registros de `extraer` y de `firma`. No los hay: corregir un
campo a mano **no gasta ni una llamada de IA**, que es lo que R17 promete.

**Punto 8 · la consola no publica datos personales.** Esa misma traza enseña
**exactamente cuatro claves** —`hash`, `paso`, `estado`, `http`— y ninguna más.
Es `js/traza.js` haciendo su trabajo: acepta esas cuatro y **tira el resto**,
así que un descuido futuro que intente registrar el DNI o las observaciones no
llega a la consola. Es un filtro con test, no una buena intención. El `hash` es
el SHA-256 del contenido del parte: identifica al parte **sin nombrarlo**, y no
es dato personal.

**Nada de esa ejecución se copia al repositorio**: los partes de `muestras/`
llevan datos personales y no se versionan.

---

## T15 · Campaña de mutación y análisis de los supervivientes — HECHA

El nivel de F-007 es **`estandar`**, y `harness/rigor.json` deja claro que ese
nivel **sí exige mutación** (`"mutacion": true`, `supervivientes_maximos: null`).
Lo que `estandar` **no** exige es **cero** supervivientes: exige que estén
**explicados** (`CHECKPOINTS.md` C4 bis).

### Primera campaña

```
$ python -m harness.mutacion --feature F-007
F-007: 1 fichero(s), 188 línea(s) de producción (origen rama, 0705d881..feature/F-007-front)
Campaña paralela: hasta 16 workers, uno por worktree.
...
20 mutantes evaluados, 14 muertos, 6 supervivientes, 0 timeouts en 13.6 s
```

Los seis supervivientes, leídos uno a uno, **no eran todos equivalentes**: tres
eran huecos de verdad, y de los que importan en la práctica.

| Superviviente | ¿Hueco real? | Qué se hizo |
|---|---|---|
| `dev_server.py:87` `timeout=300 → 301` | **Sí.** Es el timeout del proxy hacia el backend. Una extracción puede tardar decenas de segundos y la Function corta a los 230: un proxy con un timeout más corto cortaría él la petición y el front vería un 502 donde no lo hay | Test nuevo: el doble de conexión ya registraba el `timeout`, solo faltaba afirmarlo |
| `dev_server.py:147` `daemon_threads = True → False` | **Sí.** Sin hilos demonio, un `Ctrl+C` con una petición de IA en vuelo deja el proceso colgado y el humano tiene que matar la terminal | Test nuevo por atributo, sin abrir socket (R33) |
| `dev_server.py:148` `allow_reuse_address = True → False` | **Sí.** En desarrollo se para y se arranca constantemente; sin esto, el socket se queda en `TIME_WAIT` y el siguiente arranque falla con «address in use» | Test nuevo por atributo |
| `dev_server.py:169/171/175` `"=" * 60 → "=" * 61` | **No: equivalente.** Es la anchura del separador del rótulo de arranque | Se documenta y se deja vivo |

Se añadieron cuatro tests (los tres de arriba más uno que comprueba que el
destino del proxy sale de `--api` y no de un valor cableado).

### Segunda campaña, tras los tests nuevos

```
$ python -m harness.mutacion --feature F-007
...
[18/20] superviviente services/postventa-front/dev_server.py:169 [entero] log.info("=" * 60) -> log.info("=" * 61)
[19/20] superviviente services/postventa-front/dev_server.py:171 [entero] log.info("=" * 60) -> log.info("=" * 61)
[20/20] superviviente services/postventa-front/dev_server.py:175 [entero] log.info("=" * 60) -> log.info("=" * 61)
20 mutantes evaluados, 17 muertos, 3 supervivientes, 0 timeouts en 12.9 s
Informe: progress/mutacion_F-007.md
```

**20 mutantes, 17 muertos, 3 supervivientes, 0 timeouts.** Los tres son **la
misma mutación repetida** en las tres líneas del rótulo (169, 171 y 175), no
tres huecos distintos, y los tres tienen su análisis **completo** en
`progress/mutacion_F-007.md`: **ninguna sección queda en `PENDIENTE`**.

El razonamiento, resumido: un rótulo de 61 iguales en vez de 60 no cambia el
comportamiento del proxy, ni el código de salida, ni una sola respuesta HTTP;
cambia cuántos `=` ve el humano en su terminal. Fijarlo con un test compraría un
mutante muerto a cambio de un test que se rompe la próxima vez que alguien
ajuste el rótulo sin haber roto nada — justo el tipo de test que enseña a la
gente a no fiarse de la suite.

> Nota de operación: la campaña paralela crea worktrees desde `HEAD`, así que
> **exige el árbol limpio**. La primera vez avisó de ello y no arrancó; se
> commiteó y se relanzó. El árbol queda limpio para que el reviewer la
> reejecute: baja de 15 s.

---

## T16 · Portero en verde e informe — HECHA

### `ruff`: cero avisos nuevos

El portero pasó de **56 a 66 avisos** al añadir la suite del front. Los diez
eran míos (orden de imports, `noqa` de una regla no activada, comillas
sobrantes en anotaciones, alias `re.I`), no deuda previa, así que se
corrigieron:

```
$ python -m ruff check services/postventa-front --fix --output-format=concise
Found 10 errors (10 fixed, 0 remaining).
$ python -m ruff check services/postventa-front --output-format=concise
All checks passed!
```

`init.sh` vuelve a decir **56 avisos**, exactamente la deuda que había antes de
F-007: **la feature no añade ni uno**.

### Portero completo, salida real

```
$ bash harness/init.sh
[OK] Arnés v1.5.2 (2026-08-18)
[OK] Python: Python 3.12.7
[OK] Existe CLAUDE.md
[OK] Existe CHECKPOINTS.md
[OK] Existe harness/features.json
[OK] Existe harness/rigor.json
[OK] Existe specs/SPECS.md
[OK] Existe progress/current.md
[OK] Existe progress/history.md
[OK] Existe docs/ARCHITECTURE.md
[OK] Existe docs/CONVENTIONS.md
    19 features, 13 abiertas, en curso: ['F-007'], bloqueadas: ninguna
[OK] features.json válido
[OK] BACKLOG.md al día
    niveles: critico, documental, estandar; por defecto critico; umbral de cobertura 80%
[OK] harness/rigor.json y niveles declarados: válidos
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 56 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
................                                                         [100%]
16 passed in 0.51s
[OK] pytest en verde (con medición de cobertura)
    2 servicio(s): api (python), front (python)
[OK] harness/servicios.json válido
[OK] servicio api (services/postventa-api): pytest en verde (caché: árbol sin cambios desde el último verde)
........................................................................ [ 97%]
..                                                                       [100%]
74 passed in 1.80s
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: 98.3% de 116 líneas cambiadas cubiertas (114/116, umbral 80%, nivel estandar)
[OK] Rama actual: feature/F-007-front
----------------------------------------
ENTORNO LISTO. Puedes trabajar.

EXIT=0
```

---

# Evidencias

Números **medidos**, no estimados, sobre el árbol final de la rama.

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests ejecutados (F-007)** | **158 en verde, 0 rojos**: 74 de `pytest` en el servicio `front` + 84 de `node --test` | `python -m pytest -q` y `node --test "tests_js/*.test.js"` en `services/postventa-front` |
| **Tests del repositorio entero** | **1.014 en verde, 10 saltados**: 16 (raíz) + 924 (+10 skips, `api`) + 74 (`front`) | `bash harness/init.sh` |
| **Cobertura de las líneas cambiadas** | **98,3 % (114/116)**, umbral 80 %, nivel `estandar` → `[OK]` | línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Mutantes generados / evaluados** | **20 / 20** (campaña completa, sin muestreo) | `python -m harness.mutacion --feature F-007` |
| **Mutantes muertos** | **17** | ídem |
| **Supervivientes** | **3**, todos analizados; **0 secciones en `PENDIENTE`** | `progress/mutacion_F-007.md` |
| **Timeouts de mutación** | **0** | ídem |
| **Tiempo de la campaña de mutación** | **12,1 s** | ídem |
| **Tiempo de la suite del front** | **1,80 s** (`pytest`, incluye el puente a `node`); los 84 tests JS solos, **0,35 s** | salida de cada suite |
| **Tiempo de la suite de la raíz** | **0,51 s** | `bash harness/init.sh` |
| **Tiempo de la suite de la api** | **23,31 s** (924 tests; **no la toca F-007**) | la suite del servicio `api` |
| **Tiempo del portero completo** | **~10 s** (con la caché de suite del servicio `api`) | cronometrado sobre `bash harness/init.sh` |
| **Avisos de `ruff` añadidos por F-007** | **0** (el portero sigue en los 56 de deuda previa) | `bash harness/init.sh` |

Las **2 líneas de 116 sin cubrir** son `DevHandler.__init__` —llama al
`__init__` del handler de la biblioteca estándar, que exige un socket
aceptado— y el `sys.exit(main())` del `if __name__ == "__main__"`. Cubrirlas
exigiría levantar un servidor real, que es lo que R33 prohíbe.

## Ficheros tocados

**Nuevos (20):**

```
services/postventa-front/README.md
services/postventa-front/dev_front.ps1
services/postventa-front/js/api.js
services/postventa-front/js/cola.js
services/postventa-front/js/pipeline.js
services/postventa-front/js/seleccion.js
services/postventa-front/js/traza.js
services/postventa-front/tests/conftest.py
services/postventa-front/tests/test_f007_declaracion.py
services/postventa-front/tests/test_f007_dev_front_ps1.py
services/postventa-front/tests/test_f007_dev_server.py
services/postventa-front/tests/test_f007_documentacion.py
services/postventa-front/tests/test_f007_estaticos.py
services/postventa-front/tests/test_f007_js.py
services/postventa-front/tests/test_f007_sin_datos_reales.py
services/postventa-front/tests_js/api.test.js
services/postventa-front/tests_js/cola.test.js
services/postventa-front/tests_js/pipeline.test.js
services/postventa-front/tests_js/seleccion.test.js
services/postventa-front/tests_js/traza.test.js
```

**Modificados (5):**

```
harness/servicios.json                     <- se declara el servicio `front`
services/postventa-front/index.html        <- la pantalla real + los 7 scripts
services/postventa-front/js/app.js         <- pegamento de Alpine
services/postventa-front/js/config.js      <- las cinco constantes nuevas
specs/F-007-front/tasks.md                 <- casillas marcadas
```

**Recuperados sin tocar (2):** `dev_server.py` y `staticwebapp.config.json`.

**NO se ha tocado ni un fichero de `services/postventa-api/`**, ni
`harness/*.py`, ni `harness/init.sh`, ni `CHECKPOINTS.md`, ni `specs/SPECS.md`.
El arnés genérico sale intacto de F-007 (decisión D1: opción O2 descartada).

## Los siete criterios de aceptación

| | Criterio | Estado |
|---|---|---|
| 1 | Soltar PDF / ZIP / carpeta y ver el progreso por parte | **Hecho** (R1–R6, R9). Comprobación visual: T14 |
| 2 | Cada parte con su veredicto, campos y PDF, editable antes de confirmar | **Hecho** (R13–R18). Comprobación visual: T14 |
| 3 | Concurrencia limitada: una remesa larga no dispara N peticiones | **Hecho y probado**: `CONCURRENCIA_PARTES: 3` (D2) y 13 tests de la cola, incluido el del **máximo simultáneo observado** sobre las 22 tareas de una remesa como la de Mirasierra |
| 4 | Arranca en local con `dev_server.py` contra `func start` | **Hecho**; su comprobación es **MANUAL (T14)**, pendiente del humano |
| 5 | El servicio `front` declarado en `harness/servicios.json`: hoy nadie comprueba el front | **Hecho**. El portero ejecuta 158 tests del front y se pone en rojo si fallan |
| 6 | Decidido y documentado cómo se trata `dev_server.py` frente a la puerta de cobertura | **Hecho**: D1/O1 en `design.md` §9 y en el `README.md` del front, con las cuatro opciones descartadas y su motivo, y 8 tests que vigilan que siga escrito |
| 7 | `bash harness/init.sh` en verde | **Hecho**, exit 0 |

## Verificaciones MANUAL pendientes

Una sola: **T14** (R36 y criterio de aceptación 4), con sus ocho puntos
detallados más arriba. Es la única casilla de F-007 que no puede firmar un
agente, y hay que hacerla **antes de enseñar el front a Posventa**.

## Lo que queda fuera del alcance, y de quién es

| Qué | De quién |
|---|---|
| **Persistir** la remesa, los partes y las validaciones. Hoy recargar la pestaña pierde el trabajo de revisión (**D4**) | **F-019 · Endpoints de persistencia**, en `postventa-api` |
| Pintar la **cola de validación humana** guardada entre sesiones | Necesita esos endpoints: después de F-019 |
| Login, `/.auth/me`, resolver `<TENANT_ID>`, desplegar la Static Web App | **F-010** |
| Cerrar la incidencia en Sigrid y su botón | **F-008 / F-009** (y un endpoint nuevo en otro repositorio) |
| Ingesta desde buzón de correo | **F-011** |
| Reagrupar el parte de dos hojas | **F-014** |

## Desviaciones respecto a la spec, todas documentadas arriba

1. **`node --test "tests_js/*.test.js"`** en vez de `node --test tests_js`:
   desde Node 24, un directorio como argumento se intenta cargar como módulo y
   la ejecución muere con `MODULE_NOT_FOUND` sin descubrir ningún test (T4).
2. **`-Ayuda`** en vez de `-?` en `dev_front.ps1`: con `powershell -File`,
   PowerShell 5.1 no imprime nada con `-?`, y `Get-Help` solo indexa la ayuda
   por comentarios si el bloque es lo primero del fichero, lo que choca con la
   convención de abrir cada fichero con su ruta (T13).
3. **Dos comprobaciones no previstas en `design.md` §2.1**:
   `tests/test_f007_dev_front_ps1.py` —el script que ejecuta el humano— y las
   guardias de `app.js` dentro de `test_f007_estaticos.py`. Ambas **añaden**
   comprobaciones; ninguna cambia el diseño.

Las tres son hechos del entorno o comprobaciones de más, no cambios de
contrato. Ninguna toca `services/postventa-api/` ni el arnés genérico.

## T14 · MANUAL — EJECUTADA POR EL HUMANO el 2026-08-20. **Funciona.**

Front arrancado en local contra la Function, con la remesa real delante.
Veredicto del humano, literal: **«funciona a la perfección»**.

### ⚠️ Defecto de la propia T14, encontrado al ejecutarla

**El comando de la tarea no basta.** Tal y como estaba escrito —`cd` al
servicio y `func start`— **falla siempre** con:

```
ModuleNotFoundError: No module named 'pydantic'
```

El motivo está en el `sys.path` del error: `func` arrastra el **`.venv` de la
raíz del repositorio** —el del arnés, que no tiene las dependencias del
servicio— porque `cd` no cambia el entorno virtual activo. Hay que activar el
del servicio primero:

```
cd C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api
.\.venv\Scripts\Activate.ps1
func start --port 7073
```

Comprobado: el `.venv` del servicio tiene `pydantic 2.13.4`, `pymupdf`,
`psycopg` y `httpx`. **T14 se corrige con ese paso intermedio**, porque
cualquiera que siga la tarea al pie de la letra choca con el mismo error.

Segundo tropiezo, este del humano y no de la tarea: la primera vez solo se
levantó el front, y el proxy respondió `[WinError 10061] ... el equipo de
destino denegó expresamente dicha conexión`. Es el síntoma exacto de «la
Function no está arrancada»; conviene que la tarea lo nombre, porque el
mensaje de Windows no lo dice.

Ruido esperado que **no** es un fallo: `Unable to create client for
AzureWebJobsStorage`. En local, sin emulador de almacenamiento, las funciones
HTTP funcionan igual; solo importaría con disparadores de temporizador o cola,
que no tenemos.

### Las tres observaciones de diseño → **F-020**

Al ver la pantalla de trabajo con la remesa real, el humano señaló tres cosas.
**Ninguna es un fallo**: el front hace lo que promete. Son de uso, y se han
dado de alta como **F-020 · Ajustes de diseño del front**:

1. **El campo de observaciones se queda pequeño** para un texto manuscrito
   transcrito, que es de longitud variable.
2. **El PDF se ve pequeño**, que es el problema de fondo: es el documento que
   la persona está leyendo para decidir, y es lo que menos sitio ocupa.
3. **La vista del PDF está partida en dos y el reparto está al revés**: la
   tira de previsualización debe ser muy estrecha, lo justo para navegar, y
   cederle el espacio a la página.

El criterio que ordena las tres, y que conviene no perder: **en una pantalla
de revisión, el documento manda y todo lo demás le cede sitio.**

Esto es exactamente lo que una verificación manual sirve para descubrir: nada
de esto lo habría encontrado un test.

---

# Cambio 2 de la review · Trazabilidad de R5, R6, R19 y R22 (C4)

*(Escrito el 2026-08-20 por el implementer. Los cambios **1** y **3** de
`progress/review_F-007.md` los lleva el líder; esta sección cubre **solo** el
cambio 2. No se rehízo nada más de F-007, y **la tabla de resultados de T14 no
se ha tocado**: es del líder.)*

## Qué estaba mal

`specs/F-007-front/requirements.md` afirmaba que R1–R6 y R13–R22 los cubrían
`tests_js/pipeline.test.js` y `tests_js/seleccion.test.js`. Para **R5, R6, R19
y R22 no era cierto**: no existía ningún test que los comprobara. Estaban
implementados, pero solo en `index.html` y `js/app.js`, que `design.md` §3 deja
sin tests a propósito.

La salida es **mixta**, según decidió el humano: **R19 gana su test**; **R5, R6
y R22** pasan a `MANUAL (humano), T14`, con el porqué escrito.

---

## Commit `788751a` · R19 sale de `app.js` y se prueba

**Por qué este sí y los otros no.** R19 parecía presentación —«sale un
¿seguro?»— pero es una **decisión**: disparar o no disparar **una tanda de
subidas reales a SharePoint**, una por parte apto. Estaba escrita en `app.js`,
sin test **y sin punto en T14**: ni el «funciona a la perfección» del humano ni
ninguno de los ocho puntos manuales la miraban.

### El módulo nuevo

`services/postventa-front/js/confirmacion.js` — lógica pura, sin DOM, sin
Alpine y **con el reloj inyectado por parámetro**:

| Función | Qué hace |
|---|---|
| `armar(ahoraMs)` | Primer clic. Devuelve `{armadaEn}`. **Lanza** si el reloj no es un número finito: sin reloj no hay caducidad, y una confirmación que no caduca nunca es justo lo que este módulo viene a evitar |
| `pendiente(estado)` | ¿Se pinta el «¿Seguro?»? **No mira el reloj, a propósito** (ver abajo) |
| `resolver(estado, ahoraMs, [ventanaMs])` | Segundo clic. Devuelve `{dispara, estado, motivo}` |
| `cancelar()` | Vuelve al estado inicial |

**Tres decisiones de diseño, con su porqué:**

1. **La confirmación caduca al minuto** (`VENTANA_MS = 60000`). El humano dejó
   la caducidad a criterio del diseño y se implementa: un minuto sobra para
   leer «se subirán a SharePoint» y decidir, y no deja la pantalla armada
   mientras el usuario se va a comer. Sin caducidad, un clic al volver sube la
   remesa entera sin que nadie haya confirmado nada **en ese momento**.
2. **`resolver` devuelve SIEMPRE `estado: null`**, dispare o no. El armado
   queda consumido pase lo que pase. Es la defensa contra el doble clic sobre
   «Sí, archivar», que si no lanzaría **dos** tandas de subidas.
3. **`pendiente()` no mira el reloj**, y es deliberado: el reloj no es reactivo
   en Alpine, así que un panel que dependiera de él no se cerraría solo al
   caducar. La caducidad la descubre **el clic**, dentro de `resolver`, que
   cierra el panel y saca «La confirmación caducó». La alternativa —un
   `setTimeout` en `app.js`— está **prohibida por la guardia estática**, y con
   razón.

También se rechaza un **reloj que salta hacia atrás** (cambio de hora,
sincronización NTP): `transcurrido < 0` se trata como caducada. Ante la duda,
no se archiva.

### El estado es un objeto plano, no un objeto con métodos

Se descartó un `crearConfirmacion()` con estado dentro. `app.js` guarda lo que
el módulo devuelve —`{armadaEn}` o `null`— y **lo reasigna, nunca lo muta**.
Así Alpine ve el cambio sin depender de que haga proxy profundo de un objeto
con métodos dentro, que es un comportamiento del que este código no debería
colgar.

### Fase RED · las dos trazas

**Rojo 1 — el módulo no existe.** Comando exacto, desde
`services\postventa-front`:

```
node --test tests_js/confirmacion.test.js

Error: Cannot find module '../js/confirmacion.js'
Require stack:
- C:\...\services\postventa-front\tests_js\confirmacion.test.js
    at Module._resolveFilename (node:internal/modules/cjs/loader:1456:15)
    at Object.<anonymous> (...\tests_js\confirmacion.test.js:15:22) {
  code: 'MODULE_NOT_FOUND',
}
ℹ tests 1
ℹ pass 0
ℹ fail 1
```

**Rojo 2 — de aserción, que es el que vale.** Un `MODULE_NOT_FOUND` demuestra
que el fichero no está, no que los tests miren algo. Así que se escribió un
**stub trampa** que dispara siempre (`resolver: () => ({dispara: true, ...})`)
y se relanzó el mismo comando:

```
node --test tests_js/confirmacion.test.js

X f007 R19: sin armar, un solo clic NO dispara nada (2.0105ms)
v f007 R19: el segundo clic si dispara (0.2466ms)
X f007 R19: tras disparar, la confirmacion queda desarmada (0.2776ms)
X f007 R19: una confirmacion olvidada caduca y NO dispara (0.2286ms)
v f007 R19: justo en el borde de la ventana todavia dispara (1.1457ms)
X f007 R19: la ventana se puede acortar para probarla (0.2567ms)
X f007 R19: un reloj que va hacia atras no dispara (0.2332ms)
X f007 R19: un estado corrupto no dispara (0.245ms)
v f007 R19: resolver NO muta el estado que recibe (1.1638ms)
X f007 R19: pendiente() dice si hay que pintar el «seguro?» (0.4112ms)
v f007 R19: cancelar deja la confirmacion sin armar (0.1617ms)
X f007 R19: armar exige un reloj de verdad (0.408ms)
v f007 R19: la ventana por defecto es un tiempo humano (0.2129ms)
i tests 13
i pass 5
i fail 8

X failing tests:

X f007 R19: sin armar, un solo clic NO dispara nada (2.0105ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:

  true !== false

      at TestContext.<anonymous> (...\tests_js\confirmacion.test.js:23:10)
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: true,
    expected: false,
    operator: 'strictEqual'
```

**8 rojos de aserción contra un módulo que disparaba siempre**, incluidos los
dos que el humano pidió como mínimo: «un solo clic no dispara nada» y la
caducidad. Los 5 que pasaban con el stub son los que no dependen de la decisión
(el segundo clic sí dispara, el borde de la ventana, la no mutación,
`cancelar`, la cota de `VENTANA_MS`): están para fijar el contrato, no para
cazar este fallo.

**Verde, con el módulo real y el mismo comando:**

```
node --test tests_js/confirmacion.test.js

i tests 13
i suites 0
i pass 13
i fail 0
i cancelled 0
i skipped 0
i todo 0
i duration_ms 160.8604
```

### Los 13 tests

Todos con el reloj por parámetro: **ni un `setTimeout`, ni un `Date.now()`
real**. Un test de caducidad que dependa del reloj de la máquina es un test que
falla en la máquina de otro — mismo criterio que ya seguía `cola.test.js`.

Los dos que el humano exigió: `sin armar, un solo clic NO dispara nada` y
`el segundo clic sí dispara`. Los demás cubren la caducidad y su borde exacto,
el reloj hacia atrás, el estado corrupto (`{}`, `{armadaEn: "ayer"}`, `NaN`,
`undefined`, `0`, `""`), que `resolver` no muta lo que recibe, que tras
disparar queda desarmada, que `armar` exige un reloj de verdad y que la ventana
por defecto es un tiempo humano (entre 5 s y 5 min).

### Cómo quedó cableado

- **`js/app.js`**: `confirmandoArchivo: false` (un booleano suelto) pasa a
  `confirmacionArchivo: null` + `avisoArchivo: ""`, y
  `pedirConfirmacionArchivo`, `confirmacionPendiente`, `cancelarArchivo` y
  `confirmarArchivo` **delegan** en `window.Confirmacion`. Sigue siendo
  pegamento: ni una decisión dentro.
- **`index.html`**: `x-if="confirmacionPendiente()"`,
  `@click="cancelarArchivo()"` —antes la plantilla **asignaba el flag a
  mano**— y un aviso ámbar para `avisoArchivo`. Script nuevo cargado **antes**
  de `app.js`, sin `defer`.
- **`tests/test_f007_estaticos.py`**: `js/confirmacion.js` entra en
  `ORDEN_CANONICO` y `window.Confirmacion` en la guardia
  `test_f007_r36_app_js_usa_los_modulos_probados`. **Si la lógica vuelve a
  `app.js`, el test lo caza.**

---

## Commit `9a6db89` · la tabla de trazabilidad dice la verdad

En `requirements.md`, la fila «R1–R6, R13–R22» se parte en tres:

| Requisitos | Dónde se prueban |
|---|---|
| R1–R4, R13–R18, R20, R21 | `tests_js/pipeline.test.js`, `tests_js/seleccion.test.js` |
| **R5, R6, R22** | **MANUAL (humano)**, T14 |
| **R19** | `tests_js/confirmacion.test.js` |

**No se inventó ningún test de presentación** para cumplir el expediente.

### Por qué R5, R6 y R22 se verifican a mano y R13–R18 y R20–R21 no

*(La razón está escrita, además, en `requirements.md` justo debajo de la tabla,
que es donde la va a leer el siguiente. Aquí queda el mismo argumento.)*

**R5, R6, R22 y R36 son presentación pura.** Lo único que les queda por
comprobar es **que el dato acaba en la pantalla**: la fila por parte y el
`total_partes`, el mensaje de error del 400 y la vuelta al estado inicial, el
`nombre_fichero`/`carpeta`/`estado` y su enlace. Eso vive en `index.html` y
`js/app.js`, sin tests **a propósito** (`design.md` §3), porque probarlo
exigiría un DOM y una herramienta de navegador — justo la dependencia que la
feature evita (`design.md` §9). Un test de presentación que no abre un
navegador **no mira la pantalla**: da tranquilidad falsa y encima hay que
mantenerlo. Por eso se eligió corregir la tabla y no fabricarlos.

**Y la lógica que hay debajo sí está probada**, que es lo que hace aceptable la
salida manual — la mitad que se verifica a mano es la última pulgada, no el
requisito entero:

| Req | Lo que sí tiene test | Lo que se ve a mano (T14) |
|---|---|---|
| R5 | `f007 R4:` — trocear envía el multipart de la remesa tal cual (`seleccion.test.js`) | que la lista de partes aparece en pantalla |
| R6 | `api.test.js` — el `error` y los `avisos` del 400 se propagan al llamante | que la pantalla vuelve al estado inicial sin filas a medias |
| R22 | `pipeline.test.js` — qué viaja a `/api/archivar` y qué no (R29) | que la respuesta se pinta con su enlace |
| R36 | los módulos, uno a uno | que la pantalla entera funciona contra la Function |

**R13–R18 y R20–R21 son otra cosa: son decisiones, no pinturas.** Qué campo es
dudoso, qué se manda a revalidar, qué cuerpo se compone, qué parte es
archivable, por qué cola van las peticiones. Una decisión equivocada **no se ve
mirando la pantalla** —sale un número plausible y nadie sospecha—, así que se
prueba en la unidad, donde se puede afirmar el valor exacto.

Ese es el criterio, y es exactamente el que **movió a R19 de un lado al otro**:
parecía pintura y era decisión.

### T14 gana los puntos 9 y 10

Añadidos en `specs/F-007-front/tasks.md` (confirmado: están en el commit
`9a6db89`, líneas 214 y 224 del fichero), para que la próxima ejecución manual
los cubra explícitamente:

- **Punto 9 (R19)** — el **primer** clic en «Archivar los partes aptos» **no
  lanza ninguna petición**: en DevTools → Red, **cero** llamadas a
  `/api/archivar`; solo sale el «¿Seguro? Se subirán a SharePoint». La petición
  sale con el **segundo** clic. «Cancelar» cierra el aviso sin llamar a nada. Y
  si entre los dos clics pasa **más de un minuto**, el segundo **tampoco**
  archiva: sale «La confirmación caducó».
- **Punto 10 (R22)** — en el resumen salen `nombre_fichero`, `carpeta` y
  `estado` por parte, y el enlace «abrir en SharePoint» **solo** cuando la
  respuesta trae `web_url`. Desde local esto se ve con el 503 del punto 7, que
  es lo esperado; la comprobación completa es del entorno desplegado.

El enunciado de T14 pasa a nombrar también **R5, R6, R19 y R22**, no solo R36.

---

## Ficheros tocados

| Fichero | Qué |
|---|---|
| `services/postventa-front/js/confirmacion.js` | **Nuevo.** El módulo de R19 |
| `services/postventa-front/tests_js/confirmacion.test.js` | **Nuevo.** 13 tests |
| `services/postventa-front/js/app.js` | Delega en el módulo; deja de tener la lógica |
| `services/postventa-front/index.html` | `confirmacionPendiente()`, `cancelarArchivo()`, aviso de caducidad, script nuevo |
| `services/postventa-front/tests/test_f007_estaticos.py` | El módulo entra en las dos guardias |
| `services/postventa-front/README.md` | Mapa de capas |
| `specs/F-007-front/requirements.md` | Tabla de trazabilidad corregida + el porqué |
| `specs/F-007-front/tasks.md` | T14: puntos 9 y 10, y su enunciado |
| `specs/F-007-front/design.md` | El módulo, en §2.1 y §3 |

**Ni un fichero de `services/postventa-api/`.** No se tocaron
`progress/current.md` ni la tabla de resultados de T14: son del líder.

## Evidencias · cambio 2

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** | `front`: **74 passed en 2,20 s** (pytest, sin caché), y dentro va la suite JS — **97 pass, 0 fail, 0 skipped, 332,9 ms** (`node --test "tests_js/*.test.js"`, Node v24.14.1): **84 antes, +13 de R19**. `api`: **924 passed, 10 skipped en 23,98 s**, relanzada a mano porque `init.sh` la dio por caché. Raíz: **16 passed en 0,60 s** |
| **Cobertura de las líneas cambiadas** | `[OK] PUERTA COBERTURA: 98.3% de 116 líneas cambiadas cubiertas (114/116, umbral 80%, nivel estandar)` — **igual que antes**, y tenía que serlo: la puerta mide Python y este cambio no añade ni una línea de Python de producción |
| **Mutantes y supervivientes** | **20 / 3, sin cambios.** Comprobado, no supuesto: `alcance_de_feature("F-007")` devuelve **`services/postventa-front/dev_server.py: 188 líneas` y nada más**. `js/confirmacion.js` es JavaScript —fuera del alcance del motor, que solo muta `.py`— y los dos `.py` tocados están bajo `tests/`, que el arnés excluye. `progress/mutacion_F-007.md` sigue vigente tal cual. **La campaña no se reejecutó a propósito**: el árbol tenía los cambios del líder, lo que habría forzado `--workers 1`, que es justo lo que envenenó el bytecode durante la review (sección 16 de `review_F-007.md`) |
| **Tiempo de la suite** | front 2,20 s · api 23,98 s · raíz 0,60 s · JS 0,33 s |

**Limitación que conviene no tapar** (es la propuesta **P1** del reviewer, y
ahora pesa un poco más): los 13 tests nuevos son JavaScript, así que la campaña
de mutación **no los evalúa**. `js/confirmacion.js` está probado, pero ningún
mutante comprueba que sus tests muerdan. Lo que sí hay es la **fase RED con el
stub trampa** de más arriba, que es la defensa manual equivalente: 8 de los 13
fallaron contra un módulo que disparaba siempre.

`bash harness/init.sh` tras los commits: **`ENTORNO LISTO. Puedes trabajar.`,
exit 0**, con las dos suites (`api` y `front`).

## Verificaciones MANUAL pendientes de este cambio

Los **puntos 9 y 10** de T14, nuevos. El resto de T14 ya lo ejecutó el humano
el 2026-08-20. El punto 9 se comprueba **en la misma pasada** que los puntos 3,
6 y 8 del cambio 1: con la remesa cargada y DevTools → Red abierto, mirando que
el **primer** clic de archivar no genere ninguna llamada.
