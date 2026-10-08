<!-- specs/F-056-revision-bandeja-backend/requirements.md -->
# F-056 · Revisión de la bandeja en el backend: editar, descartar, aprobar y quién lo hizo — Requisitos

> **Aprobado por el humano el 2026-10-06**, con estas decisiones (detalle en
> `design.md` §15): **D-1** partir F-038 por el límite de servicio —esta ficha
> es el backend y va **antes**; la página y el cierre de la sección son
> **F-038** (`specs/F-038-bandeja-revision/`), bloqueada por esta—; **D-4**
> ubicación **obligatoria** para aprobar, **comprobada contra Sigrid en vivo**
> al aprobar y al editar (precisión del humano del 2026-10-06; ya no contra
> `config/plantilla_incidencias.yaml`); **D-8** se guarda y se enseña el
> **correo** de quien actúa; **Q-2** la lista se **pagina**; y D-2, D-3, D-5,
> D-6, D-7, D-9, D-10, D-11, D-12, D-13 y D-14 como se recomendaban (Q-1 basta
> con lo de hoy, Q-3 cualquiera de `posventa-usuarios`, Q-4 merge normal).
>
> Rama propuesta `feature/F-056-revision-bandeja-backend`. Rigor **`critico`**.
> Solo `services/postventa-api` (más el DDL de su esquema y los documentos).
> Nació como el «tramo A» de la spec de F-038 del 2026-10-06.
>
> **Q-5 RESUELTA el 2026-10-06** (medición T0 del humano, de solo lectura;
> decisión del líder dentro de la opción a recomendada): las ubicaciones
> válidas son las de la **tipología de cada unidad** (`upv.obrtplide` →
> `prmtpl.ubica`, separadas por `;`), **por unidad**, con comparación exacta
> tras recortar. En la 0677 las 44 ubicaciones usadas en sus reclamaciones
> casan todas (cubren 1.261 de 1.261). Detalle en `design.md` §16.

## 0 · De dónde sale

F-036 (cerrada el 2026-10-05) deja las incidencias del Excel de la propiedad
en `postventa.bandeja_incidencias`, **de solo lectura** y sin estado de
revisión (su R44). Volcarlas a Sigrid es **F-040**, con
`POST /api/sigrid/partes-reclamacion` (`azure-apps/sigrid_api.md` §8.9). La
ficha F-038 pide editar, descartar o aprobar con constancia de quién y
cuándo, y que solo lo aprobado sea candidato al volcado; y arrastra dos
apuntes del cierre de F-036: **las 144 filas de la 0677** importadas con el
catálogo de Sigrid del 2026-09-29, que conservan oficio o proveedor de
entonces (hay que **verlo y corregirlo**), y **las 47 con oficio ambiguo**,
que esperan la **elección del código**. Esta ficha construye todo eso en el
backend; la pantalla es F-038.

## 0.1 · Glosario

- **Valores** de una incidencia: unidad (código y nombre), ubicación,
  descripción corta, detalle, oficio (código, nombre y marca de ambiguo),
  proveedor (código, nombre y marca de ambiguo), urgencia y listado.
- **Valores importados**: los de la fila de `bandeja_incidencias`. No cambian.
- **Revisión**: una fila del histórico de una incidencia: acción, valores
  vigentes tras ella, `oid` y correo de quien la pidió, e instante UTC.
- **Valores vigentes**: los de la última revisión; sin revisiones, los
  importados.
- **Catálogo de hoy**: las dos lecturas de F-036 por `sql/read` en el momento
  de la petición: unidades de posventa de la obra y filas de `obrofc`.
- **Ubicaciones válidas de una unidad**: las que trae hoy en Sigrid la
  tipología de esa unidad (`prmtpl.ubica` de su `upv.obrtplide`), leídas con
  una **tercera lectura** por `sql/read` (R46, R48). No es la lista de
  `config/plantilla_incidencias.yaml`, que sigue siendo solo la de la
  plantilla de F-036.
- **Motivos de no aprobable**: los códigos de R21.

## 1 · Estados y acciones

- **R1.** El sistema debe **derivar** el estado de revisión de cada incidencia
  de su última revisión, sin guardarlo: `aprobada` SI la última acción es
  `aprobar`; `descartada` SI es `descartar`; y, sin revisiones o con la última
  en `editar` o `recuperar`, `editada` cuando los valores vigentes difieren de
  los importados y `nueva` cuando no.
- **R2.** El sistema debe admitir solo: desde `nueva` y `editada`, `editar`,
  `descartar` y `aprobar`; desde `aprobada`, `editar` y `descartar`; desde
  `descartada`, solo `recuperar`. SI se pide otra, ENTONCES **409
  `accion_no_permitida`** con el estado y las acciones posibles, sin leer
  Sigrid ni escribir nada.
- **R3.** CUANDO se edita una incidencia `aprobada`, el sistema debe dejarla
  `editada` (o `nueva`, por R1): pierde la aprobación y deja de ser candidata
  (R34).
- **R4.** Cada acción aceptada debe añadir **una** fila al histórico con la
  acción, los valores vigentes tras ella, el `oid` y el correo de quien la
  pide y el instante UTC. Ninguna acción modifica ni borra filas anteriores
  del histórico ni la fila de `bandeja_incidencias`.

## 2 · La petición de una acción

- **R5.** `POST /api/revision/acciones` debe recibir un objeto JSON con
  `incidencia_id`, `accion` (`editar`, `descartar`, `aprobar`, `recuperar`),
  `usuario_oid`, `usuario_correo`, `confirmado`, `revision_previa` y, según la
  acción, `valores` (solo `editar`, obligatorio) y `motivo` (solo `descartar`,
  opcional). SI el cuerpo no es un objeto, `confirmado` no es el booleano
  `true` de JSON, `usuario_oid` no es un texto de 1 a 128 caracteres tras
  recortar, `usuario_correo` no es un correo admisible (R9),
  `incidencia_id` no es un UUID, `accion` no es una de las cuatro,
  `revision_previa` no es `null` ni un entero ≥ 1, o el cuerpo lleva una clave
  que no es de esa acción, ENTONCES **400**, **antes de construir ningún
  adaptador**, sin repetir en el mensaje el `oid`, el correo ni ningún texto
  recibido.
- **R6.** SI `incidencia_id` no es de la bandeja, ENTONCES **404** sin leer
  Sigrid ni escribir.
- **R7.** SI `revision_previa` no es la `revision_id` de la última revisión
  —o no es `null` cuando no hay ninguna—, ENTONCES **409
  `revision_desactualizada`** sin escribir. La comprobación y la escritura
  ocurren en **la misma transacción**, con la fila de la incidencia bloqueada
  (`SELECT … FOR UPDATE` sobre la tabla propia): de dos acciones simultáneas
  con la misma `revision_previa`, solo se guarda una.
- **R8.** CUANDO una acción se acepta, **200** con la incidencia en la forma de
  una fila de `GET /api/revision` (R29), con su nuevo estado y su nueva
  `revision_id`; `motivos_no_aprobable` calculados contra el catálogo de hoy en
  `editar` y `aprobar`, y `null` («sin calcular») en `descartar` y `recuperar`,
  que no leen Sigrid.

## 3 · Quién: el correo de la persona (D-8)

- **R9.** `usuario_correo` es obligatorio: un texto que, recortado, tiene de 3
  a 254 caracteres, ningún blanco y exactamente una `@` con algo a cada lado.
  Se guarda recortado y tal cual (sin pasar a minúsculas). Sale de
  `/.auth/me` en el front, como el `oid` (D-13): es una **traza de quién dice
  ser**, no una identidad verificada.
- **R10.** El sistema debe guardar, en cada revisión, el `oid` **y** el correo
  de quien la pidió; y debe devolver el **correo** —nunca el `oid`— en
  `GET /api/revision` (el de la última revisión de cada incidencia) y en
  `GET /api/revision/historial` (el de cada revisión).
- **R11.** El correo **no debe** aparecer en ningún log, en ningún mensaje de
  error ni en ninguna otra respuesta que las dos de R10 y la tercera de abajo.

  > **Decisión del líder 2026-10-08** (N-1 de la review del Bloque 3): **se
  > mantiene R8**. Hay una **tercera respuesta con correo**: la **200** de
  > `POST /api/revision/acciones`, que es la fila de R29 y lleva en
  > `revisado_por` el correo de **quien acaba de actuar** (el mismo que mandó
  > en el cuerpo, recortado). Ningún error lo lleva, y el `oid` sigue sin salir
  > en ninguna respuesta (R10). `design.md` §9.
- **R12.** La excepción es **solo** de `postventa.revisiones_bandeja`: ninguna
  otra tabla del esquema gana una columna de correo, y las reglas de F-005,
  F-009, F-012, F-026, F-028 y F-036 sobre sus tablas y sus respuestas siguen
  como están (`design.md` §9).

## 4 · Editar

- **R13.** `valores` debe ser un objeto con **exactamente** `unidad_codigo`,
  `ubicacion`, `descripcion`, `detalle`, `oficio_codigo`, `proveedor_codigo`,
  `urgencia` y `listado`. CUANDO se pide editar, el sistema debe leer el
  catálogo de hoy y validar, **con comparación exacta**: la unidad es de la
  obra; la ubicación es `null` o exactamente una de las ubicaciones válidas hoy de
  **la unidad pedida** (R48: cambiar la unidad revalida la ubicación); la
  descripción,
  con los blancos colapsados, tiene de 1 a 128; el detalle, recortado, es
  `null` (también si queda vacío) o tiene como mucho 2000; el oficio es `null`
  o un código de `obrofc` de la obra; el proveedor es `null` o forma con el
  oficio una fila de `obrofc`; no hay proveedor sin oficio (salvo R15); la
  urgencia es `null`, `urgente` o `seguridad`; el listado, `null`, `primero` o
  `segundo`. SI falla algo, ENTONCES **400 `valores_no_validos`** con
  **todos** los campos que fallan (`[{campo, problema}]`), sin escribir.
- **R14.** CUANDO la edición es válida, los nombres de unidad, oficio y
  proveedor deben guardarse **tal como los da Sigrid hoy** (nunca del
  cuerpo), con las marcas de ambiguo a falso si hay código.
- **R15.** SI el oficio vigente es **ambiguo** y la edición trae
  `oficio_codigo: null`, ENTONCES se conserva el oficio ambiguo con su nombre,
  y `proveedor_codigo` solo puede ser el vigente o `null`; con otro, 400
  «elige primero el código del oficio».
- **R16.** SI los valores validados son iguales a los vigentes, ENTONCES **400
  `sin_cambios`** sin escribir.
- **R17.** Editar no cambia `duplicada_de` ni la clave guardadas en la bandeja.

## 5 · Descartar y recuperar

- **R18.** Descartar guarda los valores vigentes sin cambios y el motivo:
  opcional, recortado, `null` si queda vacío, hasta 500 caracteres (SI pasa,
  400 sin escribir). No lee Sigrid. El motivo solo sale en el historial (R33),
  nunca en un log.
- **R19.** Recuperar una `descartada` guarda los valores vigentes sin cambios;
  su estado pasa a ser el de R1. No lee Sigrid.

## 6 · Aprobar

- **R20.** CUANDO se pide aprobar, el sistema debe leer el catálogo de hoy y
  aprobar **solo SI** los valores vigentes no tienen ningún motivo de no
  aprobable; SI tienen alguno, ENTONCES **409 `incidencia_no_aprobable`** con
  **todos** sus códigos, sin escribir. La revisión de aprobar guarda los
  valores vigentes **sin cambiarlos** y su huella `sha256`.
- **R21.** Los motivos de no aprobable son exactamente, en este orden:
  `unidad_fuera_de_la_obra`; `sin_ubicacion` (no hay ubicación, D-4);
  `ubicacion_fuera_de_lista` (hay ubicación y no es una de las válidas hoy
  en Sigrid para **su unidad**, R48);
  `sin_oficio`; `oficio_ambiguo`; `oficio_fuera_de_la_obra` (no está hoy en
  `obrofc` de la obra); `par_fuera_de_la_obra` (hay proveedor y el par no es
  hoy una fila de `obrofc`); `proveedor_ambiguo`; y `duplicada` (R22). El
  sistema debe dar todos los que se cumplan.
- **R22.** Una incidencia con `duplicada_de` tiene el motivo `duplicada`
  MIENTRAS la incidencia de la que es duplicada no esté `descartada` **y** la
  clave de duplicado (`clave_de_duplicado` de F-036) calculada con los valores
  vigentes de las dos coincida. La aprobación comprueba, en la misma
  transacción, que la última revisión de esa otra incidencia es la usada para
  decidir; SI ha cambiado, 409 `revision_desactualizada`.

## 7 · Leer la bandeja para revisarla, paginada (Q-2)

- **R23.** `GET /api/revision?obra=&estado=&con_motivos=&tamano=&cursor=`
  debe validar, **antes de consultar nada**: la obra como F-036; `estado`
  ausente (= `activas`), `activas` (todas menos `descartada`), `todas` o uno de
  los cuatro estados; `con_motivos` ausente, `true` o `false`; `tamano`
  ausente (= 100) o un entero de 1 a 200; y `cursor` ausente o un cursor
  emitido por el sistema (R25). SI no, **400**.
- **R24.** El sistema debe leer **todas** las incidencias de la obra con su
  última revisión, hasta un tope de **10.000**; SI la obra tiene más,
  ENTONCES **409 `bandeja_demasiado_grande`** con el recuento, **sin truncar
  en silencio**.
- **R25.** El orden debe ser total y estable: `creada_at_utc` descendente,
  `fila_origen` ascendente (sin fila al final) e `incidencia_id`. El
  `cursor` es opaco (base64url de esa clave de la última fila de la página) y
  la página siguiente son las filas que van **después** de esa clave en ese
  orden, aplicando los mismos filtros; `siguiente` es `null` en la última
  página. *(Decisión del humano 2026-10-07: el base64url lo pone y lo quita la
  capa HTTP, por la regla de F-012; el dominio maneja la clave como JSON
  canónico. `design.md` §4.)*
- **R26.** Los filtros `estado` y `con_motivos` (motivos de no aprobable no
  vacíos) los aplica el **servidor**, con la misma función de estado (R1) y
  de motivos (R21) que las acciones.
- **R27.** La respuesta debe llevar `{obra, catalogo, resumen, filtros,
  total_filtrado, incidencias, siguiente}`; `resumen`, calculado sobre **toda**
  la obra sin filtros: `total`, `por_estado` (los cuatro), `con_motivos` y
  `por_motivo` (cada código de R21 con su recuento).
- **R28.** `catalogo` lleva lo necesario para editar: `unidades`
  (`[{codigo, nombre}]`), `ubicaciones` (`{unidad_codigo: [ubicaciones]}`,
  las válidas hoy de cada unidad de la obra, de **la misma lectura** que
  valida, R48: lo que se ofrece al editar es lo que se acepta al aprobar), `oficios` (`[{codigo, nombre, grupo:
  {etiqueta, codigos}}]`, solo los de `obrofc`), `pares` (`[{oficio_codigo,
  proveedor_codigo, proveedor_nombre}]`), `urgencias` y `listados`
  (`[{codigo, etiqueta}]`).
- **R29.** Cada incidencia lleva `incidencia_id`, `origen`, `importacion_id`,
  `fila_origen`, `creada_at_utc`, `duplicada_de`, `importados` y `vigentes`
  (con las claves de `GET /api/bandeja`), `cambios` (los campos en que
  difieren), `estado`, `revision_id`, `revisado_at_utc` y `revisado_por` (el
  correo; los tres `null` sin revisiones) y `motivos_no_aprobable`.
- **R30.** SI la obra no tiene unidades, es ambigua o su catálogo llega al
  techo, ENTONCES como `GET /api/plantilla` (404 `ObraSinUnidades`, 409
  `ObraAmbigua`, 409 `CatalogoSinVerificar`); SI Sigrid o la base no
  responden, **503** (D-14). Una sola lectura del catálogo por petición.
- **R31.** El log de `GET /api/revision` lleva solo la obra, el tamaño de la
  página, el total filtrado y cuántas volvieron.

## 8 · El historial

- **R32.** `GET /api/revision/historial?incidencia_id=`: 400 SI no es un UUID,
  404 SI no es de la bandeja, sin leer Sigrid.
- **R33.** CUANDO existe: `{incidencia_id, importada: {origen,
  importacion_id, creada_at_utc}, revisiones: [...]}`, de la más antigua a la
  más reciente, cada una con `revision_id`, `accion`, `revisado_at_utc`,
  `correo`, `campos_cambiados` (frente a la anterior, o a los importados) y
  `motivo` (solo en `descartar`). Nunca el `oid`.

## 9 · Lo aprobado, y solo eso, es candidato al volcado

- **R34.** El sistema debe ofrecer, por un puerto de la aplicación, las
  **candidatas al volcado** de una obra: las incidencias cuya última revisión
  es `aprobar`, con los valores aprobados, su huella y el instante; **ninguna
  otra**.
- **R35.** Una candidata lleva, del lado de la bandeja, lo que §8.9 necesita y
  no decide F-040: `incidencia_id`, `obra`, `unidad_codigo`, `descripcion`
  (1–128), `detalle`, `oficio_codigo` resuelto, no ambiguo y de `obrofc` el día
  de la aprobación, **`ubicacion` obligatoria** (válida en Sigrid el día de la aprobación,
  ≤ 48),
  `proveedor_codigo` opcional, y `urgencia` y `listado`. El tipo no debe
  poder construirse sin `oficio_codigo`, sin `ubicacion`, ni con oficio o
  proveedor ambiguos.

## 10 · Persistencia

- **R36.** El DDL nuevo es **un** fichero, `15_revisiones_bandeja.sql`, con
  `CREATE TABLE IF NOT EXISTS postventa.revisiones_bandeja` y su índice,
  aceptado por la guarda de `ddl.py`, **append-only**, con clave ajena a
  `bandeja_incidencias`, los `CHECK` de longitud y de ambigüedad de esa tabla,
  el de `accion` igual al `Enum` del dominio (un test los compara), las
  columnas `revisado_por` (`oid`) y `revisado_correo` (≤ 254), y sin columnas
  binarias ni JSON.
- **R37.** Ningún módulo de F-056 contiene `UPDATE`, `DELETE` ni `TRUNCATE`
  sobre `revisiones_bandeja` ni `bandeja_incidencias` (el `FOR UPDATE` del
  bloqueo no lo es), ni DDL fuera del esquema propio.
- **R38.** «La última revisión» se decide siempre por `revision_id`, no por la
  hora.

## 11 · Fronteras

- **R39.** Nada de F-056 escribe en Sigrid: solo las dos lecturas de F-036 por
  `POST /api/sql/read`; ningún módulo nuevo nombra una ruta de escritura.
- **R40.** Ninguno de los tres endpoints depende de `ARCHIVO_HABILITADO` ni de
  `CIERRE_HABILITADO`; ninguna variable de entorno nueva.
- **R41.** Ningún log lleva el `oid`, el correo, la descripción, el detalle, el
  motivo ni nombres de unidad o de proveedor: solo obra, `incidencia_id`,
  acción, resultado y recuentos. Ninguna respuesta lleva el `oid`.
- **R42.** Cualquier miembro autenticado del front (el grupo
  `posventa-usuarios`) puede ejecutar las cuatro acciones; sin roles (Q-3).
- **R43.** `oid` y correo salen del cuerpo, que el front rellena con
  `/.auth/me`, como el resto del servicio (D-13).
- **R44.** `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` (§2, §7 —el correo,
  explícito— y §8, con el recuento de endpoints anónimos) y
  `azure-apps/postventa_incidencias.md` cuentan la tabla, los tres endpoints,
  el correo, la paginación, que no escribe en Sigrid y lo que hereda F-040,
  **en el mismo trabajo**.
- **R45.** Los tests de F-036 y de F-053 siguen en verde sin tocarse; y
  `GET /api/bandeja`, la importación, la plantilla y los endpoints de
  catálogos no cambian.

## 11 bis · Las ubicaciones válidas, contra Sigrid (D-4, Q-5)

- **R46.** El sistema debe obtener las ubicaciones válidas con **una** lectura
  más por `POST /api/sql/read` de `sigrid-api` (solo lectura), parametrizada,
  **una vez por petición** —en `GET /api/revision` y en las acciones `editar`
  y `aprobar`, nunca en `descartar`, `recuperar` ni el historial— y
  compartida por todas las filas de esa petición; SI la respuesta viene con
  `truncated`, ENTONCES **409 `CatalogoSinVerificar`**, como las otras dos; y
  SI Sigrid no responde, **503** sin escribir nada (D-14).
- **R47.** La comparación es **exacta tras recortar** (la decisión 7 de
  F-036): se quitan los blancos de los extremos —de los valores de la lectura
  y de la ubicación de la incidencia— y nada más; sin plegar mayúsculas,
  tildes ni blancos interiores. Los vacíos se descartan; los de más de 48
  caracteres no se ofrecen (no cabrían en `rcp.resubi` ni en §8.9).
- **R48.** La lista sale, **por unidad**, de la tipología de cada unidad de
  posventa de la obra: una fila por unidad con su código y `prmtpl.ubica`
  (`CAST` a `nvarchar(max)`, `LEFT JOIN`: una unidad sin tipología o con
  `ubica` vacía da lista vacía), partida por `;`, cada valor recortado, sin
  vacíos ni de más de 48, en su orden y quitando solo los **repetidos
  exactos** (dos que difieren en mayúsculas o en una letra son dos
  ubicaciones: es el dato de Sigrid y se respeta tal cual, erratas
  incluidas). Una ubicación es válida para una incidencia SI y solo SI es
  exactamente uno de esos valores **de su unidad**; con lista vacía, ninguna
  lo es.

## 12 · Fuera de alcance

| Qué | Dónde |
|---|---|
| La página de revisión, la paginación en pantalla, el cierre de la sección del portal | **F-038** |
| Crear las incidencias en Sigrid, `referencia_externa`, tipo, urgencia en Sigrid, `usu`, el estado `volcada` | **F-040** |
| Proponer industrial | **F-039** |
| Aprobar o descartar varias a la vez | **F-043** |
| Agrupar proveedores (`proveedor_ambiguo` sigue falso) | **F-050** |
| Publicar el correo en el datamart | **F-048**, solo con decisión expresa |
| Reimportar una fila descartada; ver lo que traía el `v2` | Nadie (D-10, Q-1) |
| Que la plantilla Excel ofrezca las ubicaciones de la tipología de cada unidad | Ficha aparte, propuesta en `progress/spec_F-038.md` (`design.md` §16.4) |
