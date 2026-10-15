<!-- specs/F-059-volcado-sigrid-backend/requirements.md -->
# F-059 · Volcado a Sigrid en el backend: ensayo, escritura en lote y estado `volcada` — Requisitos

> **Aprobado por el humano el 2026-10-07**, con D-1 a D-14 como se
> recomendaban (`design.md` §20) y estas respuestas: **Q-1** el tipo es
> **siempre `0002`** PRIMER LISTADO POSTVENTA (el `listado` de la bandeja no
> lo decide); **Q-2** `causante: false`; **Q-3** el parte queda en **SAT** y
> **Posventa lo pasa a PTE a mano** en Sigrid; **Q-4** la verificación en
> producción es en la **obra 0626** (la UPV se elige en el momento); **Q-5**
> recrear un parte anulado, fuera de alcance; **Q-6** este trabajo actualiza
> la fila de consumidores de `azure-apps/sigrid_api.md`; **Q-7** puede volcar
> cualquiera de `posventa-usuarios` con login de Sigrid; **Q-8** el primer
> volcado masivo de la 0677 y el ajuste de `N`, más adelante y fuera de esta
> ficha.
>
> **Nace de partir F-040 (D-1, decisión del humano del 2026-10-07).** Esta
> ficha es el **tramo A**: solo `services/postventa-api`, el DDL de su
> esquema, `infra/` y los documentos, y va **antes**. La página (el panel de
> volcado en `bandeja.html`) y el cierre de los restos de F-040 en el portal
> son **F-040** (`specs/F-040-volcado-sigrid/`), bloqueada por esta. Los
> números de requisito (R1–R43) se conservan de la spec conjunta; los del
> front son R50–R59 y viven en F-040.
>
> Rama `feature/F-059-volcado-sigrid-backend`. Rigor **`critico`**:
> es **escritura en el ERP de producción**.
>
> **Conciliada con dev 2d2efd7 el 2026-10-15** (F-056 y F-060 ya en `dev`):
> cuentas, nombres reales y convivencia con F-060 en `design.md` §21; ningún
> requisito cambia de fondo. Queda pendiente del humano la lista de tests
> ajenos que hay que ampliar (R41, `design.md` §21.6 F-1).

## 0 · De dónde sale

F-040 pide que una incidencia **aprobada** en la bandeja se cree en Sigrid
como **parte de reclamación** (`con.tip 708`, serie `RS<aa>.<mm>/`) con los
mismos campos que el alta manual de Posventa
(`docs/referencia/04_alta_incidencia_sigrid.md`), en **lote**, con **dry-run
previo y confirmación**, que su **número vuelva a la bandeja** y que
**reintentar no duplique**. Esta ficha construye todo eso en el backend.

Lo que ya existe y se **consume sin cambiar**:

- **`POST /api/sigrid/partes-reclamacion`** de `sigrid-api`
  (`azure-apps/sigrid_api.md` §8.9): lote de partes de **una** obra, **una
  transacción por parte**, dry-run por defecto, idempotencia por
  `referencia_externa` con prefijo `PVI-` (en `conext` `RCPCLI`), estados
  `previsto`/`creado`/`idempotente`/`rechazado`/`no_procesado`, tope de 50
  partes y presupuesto de 150 s por lote. Desplegado, verificado y **abierto
  desde el 2026-09-25**. El parte nace en el estado inicial de la serie
  (**SAT**); no pasa a PTE.
- **F-056**: `postventa.revisiones_bandeja`, los estados derivados y
  **`candidatas_al_volcado(obra)`** (`CandidataAlVolcado`: última revisión
  `aprobar`, oficio resuelto, ubicación obligatoria, sin ambiguos, con su
  `huella`). Su design §10 deja aquí `usu`, `commit`, `referencia_externa`,
  `descripcion_larga`, `tipo`, `clase`, `forma_comunicacion`, «Causante» y el
  estado `volcada` **en tabla propia**.
- **F-060** (en `dev` desde el 2026-10-14): revisiones `editar` **del
  sistema** (`sistema:normalizar_ubicacion`) tras cada importación y a
  demanda, **solo** sobre incidencias `nueva` y `editada`, con
  `RevisionPort.registrar_lote` (la séptima operación del puerto). F-059 no la
  usa ni la cambia; por qué no puede tocar una `volcada` ni una `en_duda`, en
  `design.md` §21.5.
- **F-009**: la resolución del **login de Sigrid** de quien confirma
  (`resolver_login_de_sigrid`, correspondencia en `postventa.usuarios_sigrid`
  verificada contra `dbo.usu`).

## 0.1 · Glosario

- **Candidata**: incidencia de la bandeja cuya última revisión es `aprobar`
  (F-056 R34) y que **no** está `volcada` (R3).
- **Referencia**: `PVI-` seguido del `incidencia_id` (R5). Es la llave de la
  idempotencia en Sigrid.
- **Ensayo**: el dry-run de este servicio. Una llamada a `partes-reclamacion`
  con `commit: false`, cuyo resultado se **guarda** y se **enseña**.
- **Volcado**: la escritura. Una llamada con `commit: true`, que solo puede
  mandar lo que salió `previsto` en un ensayo vigente de la misma persona (R17).
- **Llamada**: una petición HTTP de este servicio a `partes-reclamacion`; lleva
  como mucho `N` partes (`VOLCADO_PARTES_POR_LLAMADA`, R30).
- **Evento de volcado**: una fila de `postventa.volcados_sigrid` (R32).
- **Enviado**: evento que se escribe **antes** de llamar a Sigrid con
  `commit: true` (escritura anticipada, R20).
- **En duda**: incidencia cuyo último evento de volcado es `enviado` o
  `sin_respuesta`: se pidió crear el parte y no consta qué pasó.

## 1 · Estados y candidatas

- **R1.** El estado de revisión de F-056 (R1 de F-056) se amplía con dos
  valores, **derivados y sin guardarse**, con esta precedencia:
  1. **`volcada`** SI existe algún evento de volcado de la incidencia, de
     cualquier modo (ensayo o volcado), con estado `creado` o `idempotente`;
  2. si no, **`en_duda`** SI su último evento de modo `volcado` (por
     `evento_id`) tiene estado `enviado` o `sin_respuesta`;
  3. si no, el estado de F-056 (`nueva`, `editada`, `aprobada`, `descartada`).
- **R2.** Desde `volcada` y desde `en_duda` **no** se admite ninguna acción de
  revisión (`editar`, `descartar`, `aprobar`, `recuperar`): **409
  `accion_no_permitida`** con el estado y `acciones: []`, sin leer Sigrid ni
  escribir. Se comprueba **antes** de leer Sigrid y **otra vez dentro de la
  transacción** de F-056 que bloquea la fila de la incidencia (`FOR UPDATE`),
  para que un volcado y una edición simultáneos no se crucen.
- **R3.** Son candidatas al volcado **exactamente** las incidencias en estado
  `aprobada` o `en_duda`. Una `volcada` no es candidata nunca.
- **R4.** `GET /api/revision` (F-056) debe:
  (a) llevar en cada incidencia un objeto `volcado`: `null` sin eventos de
  modo `volcado` ni parte en Sigrid; si no, `{estado, sigrid_cod,
  volcado_at_utc, volcado_por, motivo}`, donde `estado` es `volcada`,
  `en_duda`, `rechazado` o `no_procesado` (el último resultado),
  `sigrid_cod` el código del parte (solo en `volcada`), `volcado_por` el
  **correo** de quien lo volcó (D-8; nunca el `oid`) y `motivo` el código del
  último rechazo;
  (b) contar `volcada` y `en_duda` en `resumen.por_estado` (seis estados);
  (c) admitir `estado=volcada` y `estado=en_duda` como filtro; y
  (d) con `estado=activas` (o sin `estado`), devolver `nueva`, `editada`,
  `aprobada` y `en_duda` (**D-7**: ni `descartada` ni `volcada`).
- **R5.** La referencia de una incidencia es `"PVI-" + str(incidencia_id)` (el
  UUID en su forma canónica de 36 caracteres en minúsculas: 40 en total). La
  calcula **una sola función pura**; es la misma en todos los ensayos y
  volcados de la vida de la incidencia y nunca sale de otro sitio.

## 2 · El parte que se manda

- **R6.** Para cada candidata, el cuerpo de `partes-reclamacion` debe llevar
  **exactamente** estos campos (tabla campo a campo en `design.md` §5):
  `obra` = `obra_codigo`; `usu` = el login de R8; `commit` = `false` en el
  ensayo y `true` en el volcado, **siempre explícito**; y por parte
  `referencia_externa` (R5), `unidad_postventa` = `unidad_codigo`,
  `descripcion` = `descripcion`, `descripcion_larga` = `detalle` **solo si no
  es nulo** (si lo es, la clave no va), **`tipo` = `"0002"` siempre** (Q-1;
  el `listado` de la bandeja no interviene), `oficio` = `oficio_codigo`,
  `ubicacion` = `ubicacion`, `forma_comunicacion` = `1` («Escrita»,
  explícito) e `intervinientes` = `[{oficio: oficio_codigo, proveedor:
  proveedor_codigo, causante: false}]` (Q-2) si hay proveedor y `[]` si no
  (**D-9**). **Nunca** `clase`, `ide`, `cod`, `emp`, `est`, `pos`,
  propietario, persona que reclama ni urgencia (**D-10**).
- **R7.** Antes de construir el parte, el sistema debe recalcular la huella de
  F-056 (`huella_de_valores`) sobre los valores de la candidata; SI no es
  igual a la huella guardada al aprobar, ENTONCES la incidencia **no se
  manda** y sale excluida con `huella_no_coincide`.
- **R8.** El `usu` es el login de Sigrid **de la persona que pide** el ensayo o
  el volcado, resuelto con `resolver_login_de_sigrid` de F-009 (correspondencia
  confirmada, o candidato verificado por lectura contra `dbo.usu`). SI no se
  resuelve, ENTONCES **409** (`UsuarioSigridNoMapeado` o
  `UsuarioSigridInexistente`, los de F-009) **sin** llamar a
  `partes-reclamacion`. Ningún login es fijo ni técnico. Puede ensayar y volcar
  cualquier miembro de `posventa-usuarios` con login de Sigrid (Q-7).

## 3 · El ensayo: `POST /api/volcado/ensayo`

- **R9.** El cuerpo debe ser un objeto JSON con **exactamente** `obra`,
  `usuario_oid`, `usuario_correo` e `incidencias`. SI no es un objeto, la obra
  no es válida (como F-036), `usuario_oid` no es un texto de 1 a 128 tras
  recortar, `usuario_correo` no es admisible (R9 de F-056), `incidencias` no es
  una lista de 1 a `N` (R30) UUID **distintos**, o trae otra clave (incluidas
  `commit` y `confirmado`), ENTONCES **400**, **antes de construir ningún
  adaptador**, sin repetir en el mensaje el `oid`, el correo ni ningún texto
  recibido.
- **R10.** El ensayo exige el entorno (`dev` o `pro`) y la configuración de
  Sigrid completa; SI falta algo, **503 sin leer nada**. **No** exige la
  ventana `VOLCADO_HABILITADO` (**D-4**): solo lee del ERP.
- **R11.** CUANDO se pide un ensayo, el sistema debe leer las candidatas de la
  obra (`candidatas_al_volcado` más el estado de volcado) y **excluir sin
  mandarla** —con su motivo en `excluidas`— toda incidencia pedida que no sea
  de la bandeja (`no_es_de_la_bandeja`), sea de otra obra (`de_otra_obra`), no
  sea candidata (`no_es_candidata`), esté `volcada` (`ya_volcada`, con su
  `sigrid_cod`) o falle R7. Las demás van en **una** llamada con
  `commit: false`, en el orden pedido.
- **R12.** La respuesta del ensayo debe dar, por parte mandada, `incidencia_id`,
  `revision_id`, `referencia_externa`, `estado` (`previsto`, `idempotente`,
  `rechazado` o `no_procesado`), `motivo` (el **código** de §8.9 o `null`),
  `sigrid_cod` (solo en `idempotente`) y `envio` (los campos de R6 que se han
  mandado por ese parte, sin `usu`); más `ensayo_id`, `caduca_at_utc`,
  `resumen` y `excluidas`. **No** debe llevar los `cod`/`ide` provisionales de
  los `previsto` (**D-13**) ni nada de las `filas` del preview de §8.9.
- **R13.** CUANDO el ensayo recibe respuesta, el sistema debe guardar un
  evento de modo `ensayo` por parte mandada (R32), todos con el mismo
  `llamada_id` (= `ensayo_id`), y solo entonces responder. Un parte
  `idempotente` en un ensayo deja la incidencia `volcada` (R1).
- **R14.** SI la pasarela responde 400 de lote (`obra_no_encontrada`,
  `usuario_no_valido`, `serie_no_encontrada`, `estado_inicial_no_encontrado`,
  `lote_demasiado_grande`, `base_de_datos_no_permitida`), ENTONCES **409**
  `volcado_rechazado_por_la_pasarela` con ese código (o **503** si es
  `base_de_datos_no_permitida`, que es configuración de su dueño), sin guardar
  nada. SI no responde, tarda más de su tiempo, responde otro código o algo que
  no es JSON con la forma de §8.9, ENTONCES **502** sin guardar nada (es una
  lectura: repetirla es inocuo).

## 4 · El volcado: `POST /api/volcado/volcar`

- **R15.** El cuerpo debe ser un objeto JSON con **exactamente** `obra`,
  `ensayo_id` (UUID), `usuario_oid`, `usuario_correo`, `confirmado` e
  `incidencias` (lista de 1 a `N` objetos `{incidencia_id, revision_id}` con
  `incidencia_id` distintos y `revision_id` entero ≥ 1). SI no, o SI
  `confirmado` no es el booleano `true` de JSON (ni `"true"`, ni `1`),
  ENTONCES **400** antes de construir ningún adaptador, con las mismas reglas
  de mensaje que R9.
- **R16.** Las puertas, en este orden y **antes de leer nada** (ni la base ni
  Sigrid): entorno `dev` o `pro`; **`VOLCADO_HABILITADO` encendido**;
  configuración completa. SI falla una, **503 `volcado_deshabilitado`** o el de
  configuración incompleta. El interruptor se comprueba en la fábrica **y** en
  el adaptador, que se niega a mandar `commit: true` si se construyó sin él.
- **R17.** El volcado exige un **ensayo vigente** (**D-5**): `ensayo_id` tiene
  que ser una llamada de modo `ensayo` de **la misma obra**, pedida por **el
  mismo `usuario_oid`** y con menos de **30 minutos**. SI no, **409
  `ensayo_no_valido`** con `motivo` `no_existe`, `de_otra_obra`,
  `de_otra_persona` o `caducado`, sin llamar a Sigrid ni escribir.
- **R18.** Cada incidencia pedida tiene que haber salido **`previsto`** en ese
  ensayo **con la misma `revision_id`**; SI no, ENTONCES sale excluida
  (`fuera_del_ensayo` o `revision_desactualizada`) y no se manda.
- **R19.** El login (R8) se resuelve **antes** de la escritura anticipada.
- **R20.** **Escritura anticipada.** Antes de llamar a Sigrid, en **una**
  transacción de PostgreSQL con las filas de `bandeja_incidencias` de las
  incidencias pedidas bloqueadas (`FOR UPDATE`, en orden fijo de
  `incidencia_id`), el sistema debe volver a comprobar para cada una que su
  última revisión es **la del ensayo** y es `aprobar`, que no está `volcada` y
  R7; las que no, excluidas con su motivo; y por cada una que pasa, insertar un
  evento `enviado` de modo `volcado`. Solo tras el `COMMIT` se llama a Sigrid.
  SI no queda ninguna, **200** con todo excluido y **sin** llamar.
- **R21.** El volcado debe hacer **una** llamada con `commit: true` con las
  incidencias que pasaron R20, en el orden del ensayo. **Ninguna escritura se
  reintenta** por cuenta del servicio, ni ante un tiempo agotado.
- **R22.** CUANDO llega una respuesta 200 con la forma de §8.9, el sistema debe
  emparejar cada parte por `indice` **y** `referencia_externa` con lo mandado
  y guardar un evento por parte: `creado` o `idempotente` (con `sigrid_ide` y
  `sigrid_cod`), `rechazado` o `no_procesado` (con el código del motivo). SI un
  parte mandado no vuelve, vuelve con otra referencia, con un estado que no es
  de esos cuatro (`previsto` incluido) o como `creado`/`idempotente` sin `ide`
  entero o sin un `cod` de la forma `RS<aa>.<mm>/<4 dígitos>`, ENTONCES ese
  parte se guarda como **`sin_respuesta`**. El sistema decide por el estado de
  cada parte, **no** por `committed`.
- **R23.** SI la llamada no responde, se agota su tiempo, devuelve un código que
  no es 200 ni 400, no es JSON, no tiene la forma de §8.9 o dice `dry_run:
  true`, ENTONCES el sistema debe guardar **`sin_respuesta`** para cada parte
  mandado y responder **502 `volcado_sin_respuesta`** con la lista de
  incidencias en duda y un mensaje que diga que **reintentar es seguro** (la
  referencia `PVI-` no deja duplicar) y que no hay que tocar Sigrid a mano.
- **R24.** SI la pasarela responde 400 de lote en el volcado, nada se ha escrito
  en Sigrid: el sistema debe guardar **`no_procesado`** con ese código para
  cada parte mandado y responder **503** si el código es
  `escritura_reclamaciones_deshabilitada` o `base_de_datos_no_permitida`
  (configuración del dueño de `sigrid-api`) y **409** con los demás de R14.
- **R25.** SI Sigrid respondió y guardar los resultados falla, ENTONCES **500
  `volcado_sin_traza`**: las incidencias quedan `en_duda` (su último evento es
  `enviado`), el log de error lleva las referencias y los `sigrid_cod`
  recibidos, y el siguiente ensayo las encuentra `idempotente` (R13).
- **R26.** SI llega un `creado` para una incidencia que ya tenía un evento
  `creado` o `idempotente` con **otro** `sigrid_ide`, ENTONCES el sistema debe
  guardarlo igualmente, escribir un **error** en el log («posible parte
  duplicado», con las dos referencias de Sigrid) y devolverlo en `avisos`.
  Nunca se descarta en silencio.
- **R27.** Una incidencia `en_duda`, o `aprobada` con su último resultado
  `rechazado` o `no_procesado`, se puede volver a ensayar y volcar **con la
  misma referencia**. Una `volcada` no se vuelve a mandar nunca (`ya_volcada`).

## 5 · El panel: `GET /api/volcado?obra=`

- **R28.** `GET /api/volcado?obra=` debe validar la obra como F-036 (400) y
  devolver, **sin leer Sigrid**, `{obra, partes_por_llamada, resumen:
  {aprobadas, en_duda, volcadas}, candidatas: [{incidencia_id, revision_id,
  estado, ultimo_volcado}]}`, con las candidatas en el orden de R25 de F-056,
  y el mismo tope de 10.000 incidencias por obra (**409
  `bandeja_demasiado_grande`**). Sin base, **503**.

## 6 · Concurrencia

- **R29.** Una acción de revisión y un volcado sobre la misma incidencia se
  serializan por el bloqueo de su fila (R2, R20): si gana la acción, el volcado
  la excluye (`revision_desactualizada`); si gana el volcado, la acción recibe
  409. Dos volcados simultáneos de la misma incidencia pueden mandarla los dos:
  `sigrid-api` serializa por referencia (`sp_getapplock`) y el segundo vuelve
  `idempotente`; en Sigrid queda **un** parte. Nunca `pg_advisory_lock`.

## 7 · Tiempo y troceo

- **R30.** `N` = `VOLCADO_PARTES_POR_LLAMADA` (App Setting, **5** por defecto
  en el código, entero de 1 a 50). SI no es un entero de 1 a 50, el ensayo y el
  volcado responden **503** de configuración. Una petición con más de `N`
  incidencias es 400 (R9, R15). El troceo de una obra en llamadas lo hace quien
  llama (el front, F-040), no el backend (**D-6**).
- **R31.** La llamada a `partes-reclamacion` usa `SIGRID_TIMEOUT_S` y **un**
  intento (también en el ensayo). El log de cada llamada lleva su duración y
  la media por parte.

## 8 · Persistencia

- **R32.** El DDL nuevo es **un** fichero,
  `16_volcados_sigrid.sql`, con `CREATE TABLE IF NOT EXISTS
  postventa.volcados_sigrid` y sus índices (`design.md` §9), aceptado por la
  guarda de `ddl.py`: append-only; claves ajenas a `bandeja_incidencias` y
  `revisiones_bandeja`; `CHECK` de `modo` y de `estado` iguales a los `Enum`
  del dominio (un test los compara); `referencia_externa` con prefijo `PVI-`;
  `sigrid_cod`/`sigrid_ide` presentes **si y solo si** el estado es `creado` o
  `idempotente`; motivo obligatorio en `rechazado` y `no_procesado`;
  `actor_oid` y `actor_correo`; sin columnas binarias ni JSON.
- **R33.** Ningún módulo de F-059 contiene `UPDATE`, `DELETE` ni `TRUNCATE`
  sobre tablas del esquema (el `FOR UPDATE` no lo es) ni DDL fuera de él; y
  ninguna lectura selecciona `actor_oid`.

## 9 · Datos personales, logs y respuestas

- **R34.** El servicio **no manda** propietario ni persona que reclama (los
  copia `sigrid-api` de la UPV) y **descarta** las `filas` del preview de §8.9
  (llevan los identificadores de esas personas): ni se guardan, ni se
  devuelven, ni se registran. Ningún log lleva descripción, detalle,
  ubicación, nombres, `oid`, correo ni login de Sigrid: solo obra,
  `llamada_id`, modo, recuentos, duración y, por parte, referencia, estado,
  código de motivo y `sigrid_cod`. Ninguna respuesta lleva el `oid`.
- **R35.** Del motivo de un parte se guarda y se devuelve **solo el código**;
  el `mensaje` que compone la pasarela no se guarda ni se reenvía. De un 400 de
  lote, solo `details.codigo`.

## 10 · Fronteras

- **R36.** Las únicas rutas de `sigrid-api` que nombra el código nuevo son
  `POST /api/sql/read` (el login) y `POST /api/sigrid/partes-reclamacion`.
  Ningún módulo nuevo nombra `sql/write`, pasa partes a PTE, crea tareas,
  correos, gráficos, UPV ni oficios de obra.
- **R37.** `VOLCADO_HABILITADO` vale **falso por defecto en el código** y es
  una variable **aparte**: ni el cierre, ni el gráfico, ni el archivo la
  miran, y el volcado no mira `CIERRE_HABILITADO` ni `ARCHIVO_HABILITADO`.
- **R38.** `infra/desplegar_backend.ps1` debe fijar `VOLCADO_HABILITADO` en
  cada despliegue en **`false`** (**D-3**: la ventana se publica cerrada; se
  abre con su script para cada volcado), también con `-VentanasCerradas`, y
  `VOLCADO_PARTES_POR_LLAMADA`; e `infra/27_ventana_volcado.ps1` debe, como
  `19_ventana_escritura.ps1`, solo mirar sin parámetros, abrir con `-Abrir`
  tras pedir una palabra, cerrar con `-Cerrar` sin preguntar, y volver a leer
  el valor después.
- **R39.** `infra/28_volcado_lectura_sigrid.ps1` (solo `sql/read`) debe, dada
  una obra y una referencia `PVI-`, imprimir: cuántos partes `tip 708` tienen
  esa referencia en `RCPCLI`, y del parte: `cod`, código de estado, código de
  tipo, código de oficio, longitud de la ubicación, nº de intervinientes y
  marca de causante, y si su UPV es de la obra; y el `MAX(cod)` de la serie
  del mes. **Sin** descripciones, nombres, propietario ni persona.
- **R40.** `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` (§2, §3 bis, §4, §7,
  §8), `docs/DESPLIEGUE.md` (ventana del volcado) y
  `azure-apps/postventa_incidencias.md` cuentan la tabla, los tres endpoints,
  la ventana, la referencia `PVI-`, qué se escribe en Sigrid, que el parte
  **queda en SAT y Posventa lo pasa a PTE a mano** (Q-3), cómo se reconocen y
  anulan nuestros partes y qué no se hace, **en el mismo trabajo**; y la fila
  de consumidores de `azure-apps/sigrid_api.md` §10 pasa a decir que
  F-059/F-040 usan `partes-reclamacion` (Q-6; la escribe el líder al
  desplegar).
- **R41.** Los tests de F-009, F-012, F-036 y F-053 siguen en verde **sin
  tocarse**; los de F-056 solo se amplían donde fijan cuatro estados o las
  acciones posibles, citados uno a uno en el informe.

  > **Conciliación 2026-10-15, pendiente del humano (`design.md` §21.6
  > F-1).** Con `dev` 2d2efd7, el `16_…sql`, la cuenta de anónimos y la
  > cabecera de `INTEGRACION.md` ya aprobados (R32, R40, R42) obligan a
  > ampliar tests que este requisito da por intocables (de F-012, F-036 y
  > F-053) y otros de F-028, F-030–F-034, F-056 y F-060. Inventario en
  > `design.md` §21.3. Este texto no cambia hasta que el humano decida.
- **R42.** Las tres rutas nuevas van en `ANONYMOUS` como las demás
  (veinticuatro: las veintiuna de `dev` tras F-056 y F-060, más estas tres) y
  ninguna mira `CIERRE_HABILITADO` ni `ARCHIVO_HABILITADO`.

## 11 · Verificación en producción

- **R43.** MANUAL (humano), en el entorno desplegado y con su autorización
  expresa para **una** escritura, en la **obra 0626** (Q-4) y una UPV elegida
  en el momento con tipología con ubicaciones y un oficio con proveedor en
  `obrofc`: con la ventana cerrada, `volcar` responde 503 y nada cambia en
  Sigrid; el ensayo de una incidencia de prueba sale `previsto` con tipo
  `0002` y `causante: false`; con la ventana abierta, el volcado crea **un**
  parte, en **SAT**, con la referencia, tipo, oficio, ubicación e interviniente
  esperados, y su código vuelve a la bandeja (`volcada`); un segundo ensayo la
  da `ya_volcada`; la ventana vuelve a quedar **cerrada**; y el parte de prueba
  se anula desde la UI de Sigrid (NO PROCEDE, sin correo), **nunca** con
  `DELETE` y **sin pasarlo a PTE** (pasar a PTE manda correos al industrial).
  Guion en `tasks.md` Bloque 6.

## 12 · Fuera de alcance

| Qué | Dónde |
|---|---|
| El panel de volcado en `bandeja.html` y el cierre de los placeholders de F-040 en el portal | **F-040** |
| Pasar el parte a PTE (crea tareas y manda correos) | **Posventa, a mano en Sigrid** (Q-3) |
| Proponer el industrial; varios intervinientes por parte | **F-039** |
| Urgencia en Sigrid (`rcp.texurg`) | No se manda (D-10); pedirla a `sigrid-api` sería otra ficha |
| Fotos del parte | `sigrid/concepto-grafico` (otra ficha) |
| Anular o modificar un parte creado | UI de Sigrid (NO PROCEDE), nunca este servicio |
| Volver a crear un parte anulado | Nadie (Q-5) |
| El primer volcado masivo de la 0677 y el ajuste de `N` | Más adelante, fuera de esta ficha (Q-8) |
| Roles para volcar | Nadie por ahora (Q-7) |
| Volcar varias obras en una llamada | No: una obra por llamada (§8.9) |
| Publicar los volcados en el datamart | **F-048** |
| Volcado asíncrono (cola) | No (D-6) |
