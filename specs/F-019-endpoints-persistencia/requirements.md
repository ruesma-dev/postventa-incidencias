<!-- specs/F-019-endpoints-persistencia/requirements.md -->
# F-019 · Endpoints de persistencia: guardar la remesa y leer la cola

> Requisitos en notación EARS (`specs/SPECS.md`). Cada `R` se traduce a **al
> menos un test**, y el nombre del test lleva su número (`test_f019_rN_...`),
> como manda `docs/CONVENTIONS.md`.
>
> Rigor declarado: **`estandar`** (`harness/rigor.json`) → fase RED,
> cobertura ≥ 80 % de las líneas cambiadas y campaña de mutación con
> supervivientes **analizados** (no se exige cero).
>
> **Las cinco decisiones abiertas de la primera ronda están resueltas por el
> humano** (2026-08-26). Sus consecuencias están incorporadas aquí; el
> razonamiento, en `design.md` §15.

## El problema, y por qué el orden es el requisito

F-005 dejó `RepositorioPartesPort` completo y sus seis tablas creadas, y
**nadie lo llama**. Dos consecuencias verificadas:

1. **`POST /api/archivar` no puede completar nunca tal y como está
   desplegado** (defecto 15 de F-010, demostrado el 2026-08-25 contra el
   entorno real). `postventa.archivos.hash_parte` tiene una clave ajena contra
   `postventa.partes` y nada inserta el parte: el endpoint sube el PDF a
   SharePoint y **después** falla al escribir la traza con
   `ForeignKeyViolation`. Hubo que sembrar el parte a mano para verificar T18.
2. **La cola de validación humana que F-004 declara no sobrevive entre
   sesiones**, porque nada la escribe ni la lee.

De ahí que el corazón de esta feature no sean tres endpoints sino **un
orden**: el parte se guarda **ANTES** de archivarlo, y eso tiene que estar
garantizado por el código, no por la costumbre de quien llama (**R19**,
**R20**).

---

## A · `POST /api/remesa` — dejar constancia de la subida

- **R1.** CUANDO llega `POST /api/remesa` con un cuerpo JSON válido, el
  sistema debe registrar la remesa a través de
  `RepositorioPartesPort.guardar_remesa` y responder **200** con
  `{"remesa_id": <uuid>, "resultado": "creado"|"actualizado"}`.

- **R2.** CUANDO el cuerpo trae `remesa_id`, el sistema debe usar **ese**
  identificador y no generar uno nuevo: volver a llamar con el mismo
  `remesa_id` actualiza la misma fila y nunca crea una segunda.

- **R3.** CUANDO el cuerpo **no** trae `remesa_id`, el sistema debe generar
  uno con `domain.models.persistencia.nuevo_id()` y devolverlo, porque el
  llamante lo necesita para guardar después cada parte.

- **R4.** SI el cuerpo no es un objeto JSON, o le falta `nombre_origen`, o
  `num_partes` no es un entero ≥ 0, ENTONCES el sistema debe responder **400**
  diciendo **qué** falta o qué está mal, sin tocar la base de datos.

- **R5.** SI `remesa_id` viene y no es un UUID, ENTONCES el sistema debe
  responder **400** sin mandarlo a la base de datos: la columna es `uuid` y
  dejar que reviente PostgreSQL convierte un error del llamante en un error de
  infraestructura.

- **R6.** El sistema debe guardar `usuario_oid` en `NULL`. **Decisión del
  humano (D3, 2026-08-26)**: la identidad de quien sube la remesa llega en
  `x-ms-client-principal`, que es base64 **sin firma**, y guardarla invitaría a
  confundir una traza con una identidad verificada.

## B · `POST /api/parte` — guardar el parte y su veredicto

- **R7.** CUANDO llega `POST /api/parte` con `remesa_id`, `parte`,
  `extraccion` y `firma`, el sistema debe guardar el parte y su veredicto a
  través de `application/pipelines/paso_persistencia.py` y responder **200**
  con `{"hash_parte", "resultado_parte", "resultado_validacion", "avisos"}`.

- **R8.** El sistema debe **recalcular** el veredicto con las reglas de F-004
  (`domain.models.validacion.validar_parte`) a partir de la extracción y la
  firma que recibe. **Nunca** acepta un veredicto ya hecho en el cuerpo: lo
  que se decide con él es si una incidencia del ERP se archiva y se cierra.

- **R9.** CUANDO el mismo `hash_parte` se guarda por segunda vez, el sistema
  debe **actualizar** su fila —`"resultado_parte": "actualizado"`— y no crear
  una segunda: reprocesar una remesa no duplica nada
  (`docs/ARCHITECTURE.md` §9).

- **R10.** SI al cuerpo le falta un bloque (`parte`, `extraccion`, `firma`) o
  una de sus claves obligatorias, ENTONCES el sistema debe responder **400**
  diciendo **qué** falta, y sin escribir nada.

- **R11.** SI la remesa referida por `remesa_id` no consta guardada, ENTONCES
  el sistema debe responder **409** diciendo que hay que registrar la remesa
  primero (`POST /api/remesa`), y no debe quedar ninguna fila de parte.

- **R12.** El cuerpo de `POST /api/parte` **no lleva los bytes del PDF** y el
  parte se guarda sin contenido: el PDF vive en SharePoint y el disco de este
  servidor es compartido (R12/R40 de F-005).

- **R13.** SI la base de datos no responde, ENTONCES el sistema debe responder
  **503**; y SI falta su configuración, **503** nombrando **las variables** y
  jamás sus valores.

## C · `GET /api/cola` — leer la cola de validación humana

- **R14.** CUANDO llega `GET /api/cola`, el sistema debe devolver **200** con
  las entradas de `cola_validacion_humana`, ordenadas de más antigua a más
  reciente, cada una con `hash_parte`, `codigo_obra`, `numero_incidencia`,
  `observaciones`, `confianza_observaciones`, `clasificacion_firma`, `motivos`
  y `validado_at_utc`.

- **R15.** DONDE la petición traiga `limite`, el sistema debe respetarlo; si
  no lo trae, debe aplicar **50**.

- **R16.** **TOPE DURO.** El sistema **nunca** debe pedir al repositorio —ni
  devolver— más de `LIMITE_MAXIMO_COLA` (500) entradas, **venga lo que venga
  en la petición**. Una petición con un límite mayor se sirve **acotada**, no
  se rechaza: quien pide la cola es el front y un número absurdo no debe
  tumbarle la pantalla; lo que no puede es que **ninguna** llamada se lleve la
  cola entera de un tirón contra un servidor compartido de 1 vCPU.

- **R17.** SI `limite` viene y no es un entero ≥ 1, ENTONCES el sistema debe
  responder **400** sin consultar la base de datos.

- **R18.** Los tres endpoints nuevos deben registrar en el log **sólo**
  identificadores y resultados: `hash_parte`, `remesa_id`, `resultado` y
  **cuántas** entradas devolvió la cola. **Nunca** el DNI, las observaciones,
  la descripción ni la promoción. Es la regla que F-005 ya fija con
  `test_f005_logs_sin_datos_personales.py`, y estos endpoints **no la
  rompen**: el log sobrevive al parte.

## D · El orden: guardar antes de archivar

- **R19.** El sistema debe registrar la traza del archivo en estado
  `pendiente` **ANTES** de llamar al puerto de archivo. Esa escritura previa
  es la garantía de orden: la clave ajena
  `archivos.hash_parte → partes.hash_parte` sólo la admite si el parte ya
  consta guardado.

- **R20.** SI al registrar esa traza previa resulta que el parte no consta
  guardado, ENTONCES el sistema debe abortar el archivado **sin llamar al
  puerto de archivo** —ni carpeta, ni búsqueda, ni subida— y responder **409**
  diciendo que hay que guardar el parte antes (`POST /api/parte`).

- **R21.** SI la base de datos no responde al registrar la traza previa,
  ENTONCES el sistema debe responder **503** diciendo que **no se ha subido
  nada** y que se puede reintentar.

- **R22.** CUANDO la subida termina bien, el sistema debe dejar la traza en
  `archivado` con su `web_url` y su fecha; CUANDO falla, en `error` con su
  motivo. (Comportamiento de F-006 que **no cambia**: la traza previa no lo
  sustituye, lo precede.)

- **R23.** MIENTRAS la ventana de escritura esté cerrada
  (`ARCHIVO_HABILITADO` apagado), `POST /api/archivar` debe responder **503**
  **sin escribir la traza previa**: la puerta de entorno se comprueba antes de
  tocar la base de datos.

- **R24.** MIENTRAS el parte ya conste archivado, el sistema no debe escribir
  la traza previa ni volver a subir nada: la idempotencia de F-006 va **antes**
  que la traza previa, para no degradar a `pendiente` un parte ya archivado.

## E · El front llama a los endpoints en ese orden

> **Decisión del humano (D5, 2026-08-26): el cableado del front entra en
> F-019.** Sin él los endpoints existirían y nadie los llamaría, que es el
> mismo estado que esta feature viene a arreglar, un nivel más arriba.

- **R25.** CUANDO el front trocea una remesa, debe registrar la remesa
  (`POST /api/remesa`) antes de procesar ningún parte, y conservar el
  `remesa_id` para toda la sesión de esa remesa.

- **R26.** CUANDO el front obtiene el veredicto de un parte
  (`POST /api/validar`), debe guardarlo (`POST /api/parte`) **antes** de
  ofrecerlo para archivar.

- **R27.** SI el guardado de un parte falla, ENTONCES el front debe marcar ese
  parte como **no archivable** y enseñar el motivo: archivarlo fallaría
  igualmente, y hacerlo sin decirlo devuelve al usuario al defecto 15.

- **R28.** CUANDO una persona corrige un campo y se revalida el parte, el
  front debe volver a guardarlo, para que lo guardado sea lo revisado y no lo
  que dijo la IA la primera vez.

## F · Lo que hay que dejar dicho (o miente la documentación)

- **R29.** Los tres endpoints nuevos deben quedar en `ANONYMOUS`, como los
  seis actuales y por el mismo motivo estructural (el proxy de la Static Web
  App no aporta clave), y el test que fija esa anonimidad debe cubrir **los
  nueve**.

- **R30.** La cabecera de `function_app.py` debe explicar **dónde está de
  verdad la protección** desde que el servicio es backend enlazado: la
  plataforma activa Easy Auth con el proveedor `azureStaticWebApps` y el
  backend **sólo acepta lo que entra por el proxy del front**, que a su vez
  exige `authenticated` en `/*` y pertenencia al grupo de Posventa
  (`docs/DESPLIEGUE.md` §5 bis). Y debe decir qué añade `GET /api/cola` a ese
  cuadro: es el primer endpoint que devuelve **dato personal acumulado** sin
  que el llamante aporte el PDF, así que la exposición que crea es **hacia un
  usuario ya autenticado del grupo**, no hacia internet.

- **R31.** La cabecera de `services/postventa-api/tests/test_f010_endpoints_protegidos.py`
  debe dejar de afirmar que «al desplegar, los endpoints quedan **en
  internet** con `auth_level=ANONYMOUS`»: desde el enlace del backend (defecto
  13 de F-010, 2026-08-25) eso **ya no es cierto**. Debe decir el modelo
  vigente —backend enlazado + regla `/*` de la Static Web App— y **por qué el
  `auth_level` sigue en `ANONYMOUS`**: porque `FUNCTION` rompería el front.
  **El test no se relaja**: sigue teniendo que fallar si alguien cambia el
  `auth_level` sin reescribir la explicación, o al revés.

- **R32.** `docs/INTEGRACION.md` §8 debe listar los tres endpoints nuevos con
  su efecto, y su tabla de «qué NO está desplegado» debe dejar de atribuir a
  F-019 lo que ya esté hecho, sin borrar lo que siga faltando (rehidratar la
  sesión al recargar).

- **R33.** `docs/ARCHITECTURE.md` debe recoger, en el paso de **Archivo**, que
  sólo se archiva lo que **ya consta guardado**, y con qué mecanismo se
  garantiza.

- **R34.** Los endpoints nuevos **no** deben depender de `ARCHIVO_HABILITADO`:
  escriben en el esquema propio de este proyecto, no en un sistema ajeno, y
  atarlos a esa ventana dejaría sin poder guardar el trabajo de revisión justo
  cuando el archivado está cerrado, que es lo normal.

---

## Trazabilidad prevista requisito → test

| R | Test |
|---|---|
| R1–R6 | `services/postventa-api/tests/test_f019_remesa_http.py` |
| R7–R13 | `services/postventa-api/tests/test_f019_parte_http.py` |
| R14–R17 | `services/postventa-api/tests/test_f019_cola_http.py` |
| R18 | `services/postventa-api/tests/test_f019_logs_sin_datos_personales.py` |
| R19–R24 | `services/postventa-api/tests/test_f019_orden_archivado.py` |
| R11, R20 (mapeo del error de referencia) | `services/postventa-api/tests/test_f019_referencias_pg.py` |
| R25–R28 | `services/postventa-front/tests_js/persistencia.test.js` |
| R29, R30, R31 | `test_f010_endpoints_protegidos.py` (ampliado a nueve y con su cabecera corregida) |
| R32, R33 | `test_f010_integracion_expuesto.py` (ampliado), `test_f019_documentacion.py` |
| R34 | `test_f019_remesa_http.py`, `test_f019_parte_http.py`, `test_f019_cola_http.py` (los tres responden con la ventana cerrada) |

**Ninguno de estos tests toca red, base de datos ni IA**: el repositorio y el
archivador entran por inyección, como ya hacen `test_f005_paso_persistencia.py`
y `test_f006_archivar_http.py`. La única verificación que exige entorno real
es la del circuito completo contra el despliegue, marcada `MANUAL (humano)` en
`tasks.md`.
