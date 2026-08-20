<!-- specs/F-007-front/tasks.md -->
# F-007 · Front de carga y revisión — Tareas

> Rigor **`estandar`**: fase RED en los requisitos **centrales** (la cola, el
> cliente HTTP, el pipeline y la puerta de cobertura de `dev_server.py`), no
> en todo. La traza real del rojo se pega en `progress/impl_F-007.md`.
>
> Una tarea = un commit `F-007 Tn: ...`. Rama `feature/F-007-front`.
>
> **16 tareas, 5 con fase RED** (T2, T4, T7, T8 y el par T2→T3) y **una
> `MANUAL (humano)`**: T14.
>
> **El humano trabaja en PowerShell**: no admite `&&` ni comandos largos
> partidos en varias líneas. Por eso las verificaciones manuales van como
> **líneas cortas** —una por línea— o como el script `dev_front.ps1`.
>
> Comandos que se repiten (todos desde la raíz del repositorio salvo aviso):
>
> | Qué | Comando |
> |---|---|
> | Suite del front | `cd services\postventa-front` y luego `python -m pytest -q` |
> | Solo los tests JS | `node --test tests_js` (desde `services\postventa-front`) |
> | Suite del backend | `cd services\postventa-api` y luego `.venv\Scripts\python.exe -m pytest -q` |
> | Portero completo | `bash harness/init.sh` |
> | Campaña de mutación | `python -m harness.mutacion --feature F-007` |
>
> **REGLA QUE ATRAVIESA TODAS LAS TAREAS**: no se toca ni un fichero de
> `services/postventa-api/`. Si un test del front exige cambiar un contrato
> del backend, se **para y se pregunta**: sería otra feature.

---

## Fase 0 · Recuperar lo que ya existe

- [x] **T1**: Recuperar el esqueleto del front desde la rama que lo guarda,
      sin reescribir nada:
      `git checkout feature/F-007-front -- services/postventa-front`
      Deben aparecer los seis ficheros de `design.md` §1.
      **Verificación**: `git status --porcelain services/postventa-front`
      lista los seis; `bash harness/init.sh` termina en **rojo** con
      `services/postventa-front existe pero no está declarado`
      (`tests/test_servicios_declarados.py`). **Ese rojo es la fase RED de
      R31** y su traza va al informe: demuestra que hasta hoy nadie
      comprobaba el front.

## Fase 1 · El front entra en el arnés

- [x] **T2**: Declarar el servicio en `harness/servicios.json`
      (`nombre: front`, `ruta: services/postventa-front`,
      `lenguaje: python`, **sin `venv` y sin `comando_tests`**, con el porqué
      en el `$doc`), y crear `services/postventa-front/tests/conftest.py`
      (raíz del front en `sys.path` + guardia de red de sesión, R33) y
      `tests/test_f007_declaracion.py` (R31).
      **Verificación**: desde `services\postventa-front`, `python -m pytest -q`
      en verde; `bash harness/init.sh` ya **no** falla por la declaración,
      pero sigue en **rojo** en `PUERTA COBERTURA` porque las ~130 líneas
      nuevas de `dev_server.py` no las mide nadie. **Esa salida es la fase RED
      de R34** y se pega literal en el informe: es el problema que expulsó al
      front de F-001.

- [x] **T3**: Escribir `tests/test_f007_dev_server.py`: routing `/api/*` vs
      fichero estático, `do_POST` sobre ruta estática → 405, saneo de
      cabeceras (`host` y `connection` fuera, `DEV_FAKE_PRINCIPAL` dentro si
      está), backend caído → 502 **en JSON**, cabeceras de salto suprimidas
      (`transfer-encoding`, `connection`, `content-encoding`), CLI (`--port`,
      `--api`, `--root`) y arranque sin `index.html` → código 1. Todo con
      dobles: **ni un socket** (la guardia de T2 lo garantiza).
      **Verificación**: `python -m pytest -q` en verde y `bash harness/init.sh`
      con `PUERTA COBERTURA` en `[OK]` y su porcentaje. Se pega el **antes
      (T2, rojo) y el después (T3, verde)**: es la fase RED cerrada.

## Fase 2 · La lógica que se prueba (JavaScript)

- [x] **T4**: `tests_js/cola.test.js` **primero** y luego `js/cola.js`
      (`ejecutarConLimite`). Cubre R7–R12: máximo simultáneo observado ≤
      límite, orden de resultados = orden de entrada, un error no para al
      resto, `alTerminar` una vez por tarea, `limite < 1` es error.
      Añadir `tests/test_f007_js.py`, el puente que ejecuta `node --test
      tests_js` y **falla si `node` no está** (R32).
      **Verificación**: fase RED con `node --test tests_js` fallando por
      `Cannot find module '../js/cola.js'` (traza al informe); después,
      `python -m pytest -q` en verde ejecutando también los tests JS.

- [x] **T5**: `js/traza.js` y `tests_js/traza.test.js` (R28): solo pasan
      `hash`, `paso`, `estado` y `http`; cualquier otra clave se descarta,
      incluidas `observaciones` y `dni_cliente`.
      **Verificación**: `node --test tests_js` en verde; y un test que
      compruebe que el valor de un campo personal **no** aparece en la salida.

- [x] **T6**: `js/seleccion.js` y `tests_js/seleccion.test.js` (R1–R4):
      filtrado a `.pdf`/`.zip` con el recuento de descartados, selección vacía
      rechazada sin llamar a nadie, y `FormData` con **un nombre de campo
      distinto por fichero** (`fichero_0`, `fichero_1`, …).
      **Verificación**: `node --test tests_js` en verde, con un test que
      falle si dos ficheros comparten nombre de campo.

- [ ] **T7**: `tests_js/api.test.js` **primero** y luego `js/api.js` (R23–R27):
      `fetch` y `esperar` inyectados; 502 y fallo de red reintentan 2 veces
      con esperas 1 s y 3 s; 400/409/413 no reintentan y propagan el `error`
      del backend; 503 sale como `tipo: entorno`; respuesta no-JSON sale como
      `desconocido` con su código; timeout por `AbortController`.
      **Verificación**: fase RED con la traza del fallo; después
      `node --test tests_js` en verde. **Ni un test abre red**: el `fetch` es
      siempre un doble.

- [ ] **T8**: `tests_js/pipeline.test.js` **primero** y luego `js/pipeline.js`
      (R8, R13–R22, R29): extraer y firma **en paralelo** y validar solo
      después; el cuerpo de `/api/validar` se compone con las dos respuestas
      **verbatim**; un campo editado viaja con `confianza_pct` 100 (D3); las
      nueve claves siempre presentes (R18); `esArchivable` solo con `apto` +
      `archivo_y_cierre`; el `FormData` de archivar lleva **exactamente**
      cinco campos y el fichero (R29).
      **Verificación**: fase RED con su traza; después `node --test tests_js`
      en verde, con un test que falle si aparece `dni_cliente` u
      `observaciones` en el cuerpo de archivar.

## Fase 3 · La pantalla

- [ ] **T9**: `tests/test_f007_estaticos.py`: los scripts propios van al final
      del `body` y **sin `defer`**, Alpine con `3.14.1` fijo y con `defer` en
      el `head`, ningún `type="module"`, el marcador `<TENANT_ID>` intacto,
      el proxy en 7073 y `baseApi: "/api"`.
      **Verificación**: `python -m pytest -q` en verde. La fase RED de este
      test se demuestra rompiendo a propósito una copia del `index.html`
      **fuera del árbol** (añadirle `defer`) y pegando el fallo.

- [ ] **T10**: `index.html` con la pantalla real (zona de carga, progreso «N
      de M», lista de partes con semáforo, panel de detalle con los nueve
      campos y el PDF en `<iframe>` sobre un blob) y `js/config.js` con
      `CONCURRENCIA_PARTES: 3`, `TIMEOUT_PETICION_MS`, `REINTENTOS`,
      `ESPERAS_MS` y `UMBRAL_CONFIANZA`. Los siete `<script>` al final del
      `body`, sin `defer`, en orden de dependencia.
      **Verificación**: `python -m pytest -q` en verde (T9 vigila el orden y
      el `defer`) y `bash harness/init.sh` en verde.

- [ ] **T11**: `js/app.js`: estado de Alpine y pegamento. Selección, arranque
      de la cola, progreso, parte seleccionado, edición de campos,
      revalidación, confirmación y archivo, revocado del blob al cambiar de
      parte. **Sin lógica propia**: todo lo que decida algo llama a los
      módulos de T4–T8.
      **Verificación**: `bash harness/init.sh` en verde; y revisión de que
      `app.js` no contiene bucles de reintento, ni cálculo de veredicto, ni
      composición de cuerpos: eso vive en los módulos probados.

## Fase 4 · Dejar constancia

- [ ] **T12**: `services/postventa-front/README.md` (cómo se arranca, cómo se
      prueba y **el resumen de la decisión de `design.md` §9**),
      `tests/test_f007_documentacion.py` (R35) y
      `tests/test_f007_sin_datos_reales.py` (R30: ningún fichero del front
      contiene un patrón de DNI ni un PDF con partes reales).
      **Verificación**: `python -m pytest -q` en verde.

- [ ] **T13**: `services/postventa-front/dev_front.ps1`, para que el humano
      arranque el front con **una línea**: parámetros `-Puerto` (5173) y
      `-Api` (`http://localhost:7073`), UTF-8 con BOM y CRLF
      (`docs/CONVENTIONS.md`).
      **Verificación**: `powershell -File services\postventa-front\dev_front.ps1 -?`
      imprime la ayuda sin arrancar nada, y `bash harness/init.sh` sigue en
      verde.

- [ ] **T14**: **MANUAL (humano)** — R36 y el criterio de aceptación 4:
      arrancar el front en local contra la Function.

      **Terminal A** (backend; una línea por línea, sin `&&`):

      ```
      cd C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api
      func start --port 7073
      ```

      *(Si no existe `local.settings.json`, copiarlo antes de
      `local.settings.json.example` y rellenarlo. El puerto **7073** no es el
      de por defecto de `func`: es el que espera el proxy.)*

      **Terminal B** (front):

      ```
      cd C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-front
      .\dev_front.ps1
      ```

      **Qué hay que ver**, y se anota en `progress/impl_F-007.md`:

      1. `http://localhost:5173/` abre y el semáforo de servicio sale verde
         (`/api/health` a través del proxy).
      2. Al soltar un PDF de remesa, sale el número de partes y la lista.
      3. En **DevTools → Red**, con la remesa procesándose, **nunca hay más de
         6 peticiones a `/api/` en vuelo a la vez** (3 partes × 2 llamadas).
         Es la comprobación visual del criterio 3.
      4. El progreso llega a «M de M» y ningún parte se queda colgado.
      5. Al abrir un parte se ve su PDF y sus campos con la confianza.
      6. Corregir un campo y revalidar cambia el veredicto **sin** llamar a
         `/api/extraer` ni a `/api/firma` (se ve en Red).
      7. Pulsar archivar responde **503 «este entorno no archiva»**. **Es lo
         correcto**: la puerta de entorno de F-006 está apagada por defecto.
         **No se toca esa puerta para «arreglarlo»**, y desde local **no se
         sube nada a SharePoint**.
      8. En la consola del navegador **no aparece** ningún DNI ni ninguna
         observación (R28).

      **Nada de esa ejecución se copia al repositorio**: los partes de
      `muestras/` llevan datos personales y no se versionan.

## Fase 5 · Puertas del rigor `estandar`

- [ ] **T15**: Campaña de mutación y análisis de los supervivientes.
      **Verificación**: `python -m harness.mutacion --feature F-007` genera
      `progress/mutacion_F-007.md` con sus totales, y **cada superviviente
      tiene su sección de análisis completada** (ninguna en `PENDIENTE`).
      Nivel `estandar`: no se exigen cero supervivientes, se exige que estén
      **explicados** (`CHECKPOINTS.md` C4 bis). Si la campaña baja de 5
      minutos, el reviewer la reejecutará: se deja el árbol limpio.

- [ ] **T16**: Ejecutar `bash harness/init.sh` **en verde** (exit 0), con la
      suite del front ejecutándose y `PUERTA COBERTURA` en `[OK]` (umbral
      80 %), y escribir el informe `progress/impl_F-007.md` con la sección
      **Evidencias**: tests ejecutados y resultado, cobertura de las líneas
      cambiadas, mutantes y supervivientes, y tiempo de la suite.
      **Verificación**: `bash harness/init.sh` termina con
      `ENTORNO LISTO. Puedes trabajar.` y exit code 0.

---

## Antes de empezar: decisiones que el humano puede querer contestar

Ninguna **bloquea** (ver `design.md` §13). Con silencio se implementa la
recomendación:

- **D1** — `dev_server.py` frente a la puerta de cobertura → **O1: probarlo**
  (T3). Si el humano prefiere exclusiones configurables, es una feature de
  `arnes-base`, no de F-007.
- **D2** — límite de concurrencia → **3 partes** (T10, constante de
  `config.js`).
- **D3** — confianza de un campo corregido a mano → **100** (T8).
- **D4** — la remesa **no se persiste**: recargar la pestaña pierde el
  trabajo. Necesita endpoints nuevos en `postventa-api`: feature aparte.
- **D5** — navegador soportado: Edge/Chrome (`webkitdirectory`).
