<!-- specs/F-007-front/requirements.md -->
# F-007 · Front de carga y revisión — Requisitos (EARS)

> Contrato de partida: la entrada `F-007` de `harness/features.json`
> (`description` + **siete** criterios `acceptance`). Estos requisitos los
> desarrollan; no los amplían.
>
> Rigor declarado: **`estandar`**. Exige tests trazables, **fase RED en los
> requisitos centrales**, cobertura de las líneas cambiadas ≥ 80 % y campaña
> de mutación con los supervivientes documentados y analizados. **No** exige
> cero supervivientes ni fase RED en todo: no se infla la spec como si fuera
> `critico`.
>
> **Ni un dato real.** Los códigos y textos de ejemplo de este documento están
> **inventados** (`0677`, `RS26.08/0123`). Los partes de verdad llevan DNI y
> observaciones manuscritas de clientes: no entran en el repositorio, ni en
> esta spec, ni en fixtures, ni en la consola del navegador.

## Alcance

F-007 construye **la pantalla** que hoy no existe: cargar una remesa, verla
trocearse, ver el veredicto parte a parte, corregir lo dudoso y archivar lo
apto. Todo contra endpoints que **ya existen y no se tocan**.

Y cierra un agujero del arnés: **hoy nadie comprueba el front**. Al terminar
F-007, `bash harness/init.sh` ejecuta una suite del front y se pone en rojo si
falla.

Fuera de alcance, explícitamente:

| Qué | De quién es |
|---|---|
| Cualquier cambio en `services/postventa-api/` (endpoints, dominio, pipelines) | Ya está hecho: F-002 … F-006 |
| **Persistir** la remesa, los partes, las validaciones o la cola | No hay endpoint que lo haga (ver `design.md` §10, D4) |
| Pintar la **cola de validación humana** guardada entre sesiones | Necesita ese endpoint: futura, no F-007 |
| Cerrar la incidencia en Sigrid, y su botón | F-008 / F-009 |
| Desplegar la Static Web App, resolver `<TENANT_ID>`, crear el grupo de Entra | **F-010** |
| Login, `/.auth/me`, nombre del usuario en la cabecera | **F-010** (en local el backend va con `AUTH_DISABLED`) |
| Ingesta desde buzón de correo | F-011 |
| Reagrupar el parte de dos hojas | F-014 |

## Vocabulario

- **Remesa**: lo que el usuario carga de una vez (un PDF, un ZIP o el
  contenido de una carpeta). Puede traer varios ficheros.
- **Parte**: la unidad de trabajo (`docs/ARCHITECTURE.md`, semántica 1). Un
  PDF de remesa contiene N partes de N incidencias distintas. **Nada de la
  pantalla se razona «por fichero»** después de `/api/split`.
- **Parte en curso**: el que tiene alguna petición viva contra el backend.
- **Plaza**: cada uno de los huecos del limitador de concurrencia. Un parte en
  curso ocupa exactamente una plaza.
- **Semáforo**: verde = `apto` + `archivo_y_cierre`; ámbar =
  `cola_validacion_humana`; rojo = `revision_manual`. Son los valores que
  emite `/api/validar` (F-004), no una escala nueva.
- **Campo editado**: un campo cuyo valor ha corregido una persona en pantalla.
- **Traza del front**: la única forma de registro que el front puede emitir
  (`hash` del parte, paso, estado, código HTTP). Nunca valores de campos.

---

## 1 · Carga de la remesa

**R1.** CUANDO el usuario suelta sobre la zona de carga uno o varios ficheros
`.pdf` o `.zip`, el sistema debe aceptarlos, listar su nombre y su tamaño, y
**no enviar nada** hasta que el usuario lo confirme.

**R2.** CUANDO el usuario elige una carpeta con el selector de carpeta del
navegador, el sistema debe quedarse solo con los `.pdf` y `.zip` que contenga
y decir **cuántos ficheros ha descartado** y por qué.

**R3.** SI la selección no contiene ningún `.pdf` ni `.zip`, ENTONCES el
sistema debe rechazarla en el navegador —**sin** llamar a `/api/split`— y
explicar qué formatos admite.

**R4.** CUANDO el usuario confirma la carga, el sistema debe enviar **una
sola** petición `POST /api/split` en `multipart/form-data` con **un nombre de
campo distinto por fichero** (`fichero_0`, `fichero_1`, …).

> Por qué el nombre distinto: el backend lee `req.files.values()`, que
> devuelve **un valor por clave**. Dos ficheros con el mismo nombre de campo
> se perderían en silencio, y una remesa de 3 PDFs entraría como 1.

**R5.** CUANDO `/api/split` responde 200, el sistema debe mostrar
`total_partes`, los `avisos` de la remesa y **una fila por parte** en estado
`pendiente`, identificada por su `hash`.

**R6.** SI `/api/split` responde 400, ENTONCES el sistema debe mostrar el
`error` y los `avisos` que trae la respuesta, y volver al estado inicial sin
dejar filas a medias.

---

## 2 · Proceso parte a parte y límite de concurrencia

**R7.** MIENTRAS queden partes pendientes, el sistema debe mantener **como
mucho `CONCURRENCIA_PARTES` partes en curso a la vez** —valor por defecto
**3**, declarado en `js/config.js`— y no arrancar el siguiente hasta que uno
termine.

> Es el criterio de aceptación 3: «una remesa larga no dispara N peticiones a
> la vez». La remesa real de Mirasierra son **22 partes**. El porqué del 3
> está en `design.md` §5.

**R8.** CUANDO un parte entra en curso, el sistema debe pedir
`POST /api/extraer` y `POST /api/firma` **en paralelo** para ese parte, y solo
cuando las dos hayan respondido pedir `POST /api/validar` con los dos cuerpos
**tal y como los devolvieron los endpoints**, sin montar ninguno a mano.

**R9.** El sistema debe mostrar el progreso como «N de M partes terminados»,
actualizado cada vez que un parte termina —con veredicto **o** con error—, y
debe llegar a N = M cuando la remesa acaba.

**R10.** SI un parte termina en error, ENTONCES el sistema debe **seguir con
los demás**, dejar ese parte marcado como erróneo con su motivo y ofrecer
reintentarlo él solo.

**R11.** CUANDO el usuario reintenta un parte erróneo, el sistema debe volver
a pasarlo por la **misma** cola, respetando el límite de R7.

**R12.** El sistema debe abortar toda petición que pase de
`TIMEOUT_PETICION_MS` (por defecto **180000**) y tratarla como error
transitorio, para que una petición colgada no deje una plaza ocupada para
siempre.

---

## 3 · Semáforo, revisión y corrección

**R13.** CUANDO un parte recibe su veredicto, el sistema debe pintar el
semáforo según `veredicto` y `destino` (verde / ámbar / rojo, ver Vocabulario)
y listar **todos** los `motivos` con su `texto`.

**R14.** CUANDO el usuario abre un parte, el sistema debe mostrar sus nueve
campos con su `confianza_pct`, la clasificación de la firma y **el PDF de ese
parte**, construido a partir del `contenido_b64` que devolvió `/api/split`.

**R15.** El sistema debe destacar en pantalla los campos con `confianza_pct`
**por debajo de 50** —el umbral del dominio (`domain/models/firma.py`)— para
que se miren antes de confirmar nada.

**R16.** CUANDO el usuario corrige el valor de un campo, el sistema debe
marcarlo como **editado** en pantalla y enviarlo en la siguiente validación
con `confianza_pct` **100** (decisión **D3**), sin tocar el resto del cuerpo
ni la `traza`.

**R17.** CUANDO el usuario pide revalidar un parte corregido, el sistema debe
llamar **solo** a `POST /api/validar` —nunca a `/api/extraer` ni a
`/api/firma`— y sustituir el veredicto anterior por el nuevo.

> `/api/validar` no gasta IA: revalidar un parte corregido es gratis, y esa es
> justo la razón de que exista separado (`interface_adapters/api/validar.py`).

**R18.** SI el usuario deja vacío un campo obligatorio del cuerpo de
validación, ENTONCES el sistema debe enviar igualmente las nueve claves
—`valor: null` si está vacío— porque el backend exige las nueve y responde 400
si falta una.

---

## 4 · Archivo

**R19.** MIENTRAS haya partes en verde sin archivar, el sistema debe ofrecer
un botón de archivar que exige **confirmación explícita** del usuario antes de
la primera petición.

**R20.** CUANDO el usuario confirma el archivo, el sistema debe llamar
`POST /api/archivar` **una vez por parte apto**, por la **misma** cola y con
el mismo límite de R7, enviando exactamente el fichero y los campos `hash`,
`codigo_obra`, `numero_incidencia`, `veredicto` y `destino`.

**R21.** El sistema **nunca** debe llamar a `/api/archivar` para un parte cuyo
veredicto no sea `apto` con destino `archivo_y_cierre`, ni siquiera si el
usuario pulsa el botón dos veces.

**R22.** CUANDO `/api/archivar` responde 200, el sistema debe mostrar
`nombre_fichero`, `carpeta`, `estado` y, si viene, un enlace a `web_url`.

---

## 5 · Errores del backend

**R23.** SI una petición responde **502** o falla la conexión, ENTONCES el
sistema debe reintentarla como mucho **2 veces**, con espera creciente (1 s y
3 s), antes de darla por fallida.

> `docs/CONVENTIONS.md`: «errores transitorios de red: reintentos con backoff,
> nunca bucle desnudo».

**R24.** SI una petición responde **400**, **409** o **413**, ENTONCES el
sistema **no** debe reintentarla y debe mostrar el texto del campo `error` de
la respuesta.

**R25.** SI `/api/archivar` responde **503**, ENTONCES el sistema debe decir
que **este entorno no archiva** —es la puerta de entorno, no un fallo— y no
reintentar.

**R26.** SI una respuesta no es JSON —el proxy o la Static Web App pueden
devolver HTML—, ENTONCES el sistema debe mostrar el código HTTP y seguir
funcionando, sin lanzar una excepción sin capturar.

**R27.** CUANDO carga la pantalla, el sistema debe consultar `GET /api/health`
y mostrar el estado del servicio, como ya hace hoy.

---

## 6 · Datos personales

**R28.** El sistema **nunca** debe escribir el valor de `observaciones` ni de
`dni_cliente` en la consola del navegador, en `localStorage`, en
`sessionStorage`, en la URL ni en ningún otro registro. La traza del front
lleva **solo** `hash`, paso, estado y código HTTP.

**R29.** El sistema **nunca** debe enviar a `/api/archivar` más campos que los
de R20: ni DNI, ni observaciones, ni descripción.

**R30.** El repositorio **no** debe contener ningún parte real: los fixtures
de la suite del front son PDFs mínimos construidos en el propio test o
cadenas inventadas.

---

## 7 · El front, dentro del arnés

**R31.** El repositorio debe declarar el servicio del front en
`harness/servicios.json`, y `bash harness/init.sh` debe **ejecutar su suite** y
terminar en rojo si esa suite falla.

> Hoy `tests/test_servicios_declarados.py` ya obliga a ello: en cuanto
> `services/postventa-front/` vuelva al árbol, ese test falla mientras el
> servicio no esté declarado. El criterio de aceptación 5 tiene por tanto un
> guardián que ya existe.

**R32.** CUANDO se ejecuta la suite del front, el sistema debe ejecutar
también los tests unitarios de JavaScript; y SI `node` no está disponible,
ENTONCES la suite debe **fallar diciendo que falta**, nunca saltárselos en
silencio.

**R33.** La suite del front **no** debe abrir ninguna conexión de red real,
igual que la del backend: se comprueba con una guardia de sockets propia.

**R34.** `dev_server.py` debe quedar cubierto por tests, de forma que la
puerta de cobertura de `bash harness/init.sh` mida sus líneas cambiadas en vez
de contarlas como no medidas.

**R35.** La decisión sobre cómo se trata `dev_server.py` frente a la puerta de
cobertura debe quedar **escrita** en `design.md` §9 y resumida en
`services/postventa-front/README.md`, con las opciones descartadas y su
motivo.

**R36.** CUANDO se ejecuta `python dev_server.py --api http://localhost:7073`
desde `services/postventa-front`, el front debe servirse en
`http://localhost:5173` y proxiar `/api/*` a la Function levantada con
`func start`. *(Verificación `MANUAL (humano)`: T14.)*

**R37.** `bash harness/init.sh` debe terminar en verde (exit 0) con el
servicio del front declarado y su suite ejecutándose.

---

## Trazabilidad requisito → test

| Requisitos | Dónde se prueban |
|---|---|
| R1–R4, R13–R18, R20, R21 | `tests_js/pipeline.test.js`, `tests_js/seleccion.test.js` (node:test) |
| **R5, R6, R22** | **MANUAL (humano)**, T14 — ver la nota de abajo |
| **R19** | `tests_js/confirmacion.test.js` |
| R7–R12 | `tests_js/cola.test.js` |
| R23–R27 | `tests_js/api.test.js` |
| R28–R29 | `tests_js/traza.test.js`, `tests_js/pipeline.test.js` |
| R30 | `tests/test_f007_sin_datos_reales.py` |
| R31, R37 | `tests/test_servicios_declarados.py` (raíz, ya existe) + `tests/test_f007_declaracion.py` |
| R32 | `tests/test_f007_js.py` |
| R33, R34 | `tests/test_f007_dev_server.py` |
| R35 | `tests/test_f007_documentacion.py` |
| R36 | **MANUAL (humano)**, T14 |

Nombres trazables, según `docs/CONVENTIONS.md`: en Python
`test_f007_rN_<qué>`; en los tests de node, el nombre del `test()` empieza por
`f007 RN:`.

### Por qué R5, R6, R22 y R36 se verifican a mano y R13–R18 y R20–R21 no

*(Corregido en la review de F-007: hasta entonces la tabla decía que los
cubrían `pipeline.test.js` y `seleccion.test.js`, y no era cierto.)*

**R5, R6, R22 y R36 son presentación pura**: pintar `total_partes` y una fila
por parte, pintar el `error` y volver al estado inicial, pintar
`nombre_fichero`/`carpeta`/`estado` y el enlace a `web_url`. Lo único que
queda por comprobar en ellos es **que el dato acaba en la pantalla**, y eso
vive en `index.html` y en `js/app.js`, que `design.md` §3 deja sin tests **a
propósito**: probarlos exigiría un DOM y una herramienta de navegador, que es
justo la dependencia que la feature evita (§9). La alternativa —inventar tests
de presentación que en realidad no miran la pantalla— sería cumplir el
expediente sin ganar seguridad.

**Y la lógica que hay debajo de esos cuatro sí está probada**, que es lo que
hace aceptable la salida manual:

| Requisito | Lo que sí tiene test | Lo que se ve a mano (T14) |
|---|---|---|
| R5 | `f007 R4:` — trocear envía el multipart de la remesa tal cual (`seleccion.test.js`) | que la lista de partes aparece en pantalla |
| R6 | `api.test.js` — `error` y `avisos` del 400 se propagan al llamante | que la pantalla vuelve al estado inicial sin filas a medias |
| R22 | `pipeline.test.js` — qué viaja a `/api/archivar` y qué no (R29) | que la respuesta se pinta con su enlace |
| R36 | los módulos, uno a uno | que la pantalla entera funciona contra la Function |

**R13–R18 y R20–R21 son distintos**: no son «pintar un dato», son **decisiones**
—qué campo es dudoso, qué se envía a revalidar, qué cuerpo se compone, qué
parte es archivable, por qué cola van las peticiones—. Una decisión equivocada
no se ve mirando la pantalla, así que se prueba en la unidad.

**R19 era el caso peor y por eso cambió de bando**: parecía presentación
—«sale un ¿seguro?»— pero es una **decisión** (disparar o no disparar una tanda
de subidas reales a SharePoint) que estaba escrita en `app.js`, sin test **y
sin punto en T14**. La lógica se sacó a `js/confirmacion.js` y se prueba como
el resto. Lo que queda a mano es solo su pintura, y ahora tiene punto propio en
T14.
