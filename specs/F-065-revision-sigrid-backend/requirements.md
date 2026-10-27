<!-- specs/F-065-revision-sigrid-backend/requirements.md -->
# F-065 · Las reclamaciones de Sigrid en la revisión, en el backend: leerlas y cruzarlas con la bandeja — Requisitos

> **Nace de partir F-064 (Q-1, aprobada por el humano el 2026-10-21).** Esta
> ficha es el **tramo A**: solo `services/postventa-api`, `infra/` y los
> documentos, y va **antes**. La página (el panel de Sigrid en `bandeja.html`)
> es **F-064** (`specs/F-064-bandeja-con-sigrid/`), bloqueada por esta y por
> F-038. Los números de requisito (R1–R40) se conservan de la spec conjunta;
> los de la página son R50–R69 y viven en F-064. Orden: **F-038 → F-065 →
> F-064 → F-040**.
>
> Rama `feature/F-065-revision-sigrid-backend`. Rigor **`critico`**: lee el ERP
> de producción y sirve datos personales de clientes a la página.
>
> **Spec aprobada por el humano el 2026-10-21** (`design.md` §14). Q-1 dos
> tramos, este es F-065; **Q-2** se leen **todas** las reclamaciones de la
> obra, de cualquier estado y fecha, y se filtran en pantalla; **Q-3** misma
> unidad + oficio + ubicación, el emparejamiento `PVI-` con sus avisos de
> coherencia, y misma unidad + descripción parecida; **Q-4** no bloquea; **Q-5**
> ruta aparte; **Q-6** los datos personales **sí** se enseñan en la página,
> nunca en logs, ni en el repositorio, ni en nuestra base; Q-7 a Q-10 como se
> recomendaban. Y las tres que derivan de ellas: **N-1** una sola lectura con
> el techo de la pasarela, **500.000** filas, comprobando `truncated`; **N-2**
> «descripción parecida» por Jaccard, umbral 50 y al menos 2 palabras en
> común; **N-3** **todo en el listado, una sola ruta** (la ficha bajo demanda
> desaparece), con la lista cerrada de campos de R33, para poder buscar y
> filtrar por propietario o teléfono en la página.

## 0 · De dónde sale

Petición del humano (2026-10-20): «en la bandeja de revisión deberán poder
verse tanto las incidencias que queremos importar que salen del Excel, como
las que ya hay en Sigrid y si hay conflictos entre ellas». Hoy la bandeja solo
se compara consigo misma (`duplicada`, F-036/F-056) y no lee las reclamaciones
de la obra en Sigrid. Lo que existe y se reutiliza **sin cambiarlo**:

- `GET /api/revision` (F-056, F-059, F-060) y su medición `F-060 tiempos del
  listado` (p50 ≈ 5 s, máximo ≈ 13 s; F-061 lo optimizará).
- El estado derivado de cada incidencia, con `volcada` y `en_duda` (F-059), y
  su `sigrid_cod`.
- La referencia `PVI-<incidencia_id>` que F-059 manda y la pasarela guarda en
  `conext` `RCPCLI` (`azure-apps/sigrid_api.md` §8.9).
- El adaptador de lectura de F-036 (`AdaptadorCatalogoSigridApi`), que F-056
  ya heredó sin tocarlo.
- `clave_de_ubicacion` (F-060), `normalizar_para_clave` y `plegar` (F-036).

## 1 · La ruta y lo que se mira antes de leer nada

**R1.** CUANDO llega `GET /api/revision/sigrid?obra=<código>`, el sistema debe
normalizar la obra con `normalizar_codigo_obra` (F-036) y, SI no vale,
ENTONCES responder **400** `peticion_invalida` sin construir ningún adaptador,
sin leer Sigrid y sin leer la base. Cualquier otro parámetro se ignora.

**R2.** El sistema debe construir el lector de reclamaciones de Sigrid
**antes** que el repositorio de la revisión, con las dos puertas de las
lecturas de F-036 y en ese orden —entorno (`dev` o `pro`) y configuración—:
fuera de esos entornos, **503** sin abrir ninguna conexión; sin configuración,
**503** nombrando las variables y **nunca** sus valores. No mira ninguna
ventana de escritura (`CIERRE_HABILITADO`, `ARCHIVO_HABILITADO`,
`VOLCADO_HABILITADO`).

**R3.** Cada petición debe hacer **exactamente una** lectura de la base
(`RevisionPort.listar` con el tope de F-056) y **como mucho una** de Sigrid
(`POST /api/sql/read`), en ese orden, y ninguna otra.

**R4.** SI la bandeja de la obra pasa de 10.000 incidencias, ENTONCES **409**
`bandeja_demasiado_grande` con el recuento (`RevisionPort.contar`), **sin leer
Sigrid**.

## 2 · Qué se lee de Sigrid

**R5.** *(Q-2.)* La consulta debe traer **todas** las reclamaciones del tipo de
concepto configurado (`SIGRID_TIP_RECLAMACION`, 708) cuya unidad de posventa es
de una obra con ese código **literal y recortado** (el filtro de las lecturas
de F-036), **de cualquier estado y de cualquier fecha**. El estado se lee **por
su código** contra `conest`, nunca por número (C3). **Todo valor viaja como
marcador `?`**: el campo `RCPCLI`, el patrón `PVI-%`, el tipo y la obra.

**R6.** *(Q-6 y N-3.)* La consulta debe leer **solo** estas columnas, en una
sola lectura: la referencia de la obra de la unidad (`upv.obride`, para contar
obras; no sale de la aplicación), `con.cod`, el código de estado, `con.fec`, el
código de la unidad, código y nombre del oficio (`auxofc`), código y nombre del
tipo de reclamación (`auxtrcp`), `rcp.resubi`, `con.res`, la referencia
`RCPCLI` **solo si empieza por `PVI-`** (si no, `NULL`), y los campos de
**R33**.

**R7.** *(Retirado el 2026-10-21 por Q-2: no hay fecha de corte; se lee todo.)*

**R8.** *(N-1, aprobada el 2026-10-21.)* La lectura debe pedir `max_rows` igual
a `TOPE_RECLAMACIONES_OBRA`, **500.000**, el `MAX_ALLOWED_ROWS` de la instancia
desplegada de la pasarela (`azure-apps/sigrid_api.md` §4.1), constante del
dominio. SI la respuesta viene con `truncated`, o con ese número de filas o
más, ENTONCES **409** `reclamaciones_sin_verificar` con el número de filas y
**sin calcular ningún conflicto**: nunca conflictos a medias. SI la respuesta
está mal formada o la pasarela no responde, ENTONCES **503** sin nada a medias.
Lo transitorio se reintenta con la política de F-036 (`SIGRID_REINTENTOS`,
`SIGRID_TIMEOUT_S`), que corta muy por debajo de los 230 s del balanceador.

**R9.** SI las filas son de más de una obra (dos `obride` distintos),
ENTONCES **409** `obra_ambigua`, como el catálogo de F-036. SI no vuelve
ninguna fila, ENTONCES **200** con la lista vacía.

## 3 · Emparejar por la referencia `PVI-`

**R10.** Una reclamación cuya referencia es `PVI-` seguido de un UUID que es el
`incidencia_id` de una incidencia **de la bandeja de esa obra** debe quedar
**emparejada** con ella. El prefijo y el UUID se comparan **sin distinguir
mayúsculas**, como la intercalación de la pasarela. Una referencia `PVI-` que
no es un UUID, o que no es de ninguna incidencia de la obra, queda sin
emparejar y con el hallazgo **`referencia_desconocida`** (aviso).

**R11.** CUANDO una incidencia que **no** está `volcada` tiene una reclamación
emparejada, el sistema debe dar el hallazgo **`ya_en_sigrid`** (severidad
**conflicto**) con el código de esa reclamación.

**R12.** CUANDO una incidencia está `volcada`, el sistema debe dar, con su
código: **`volcada_no_encontrada`** (aviso) si ninguna reclamación está
emparejada con ella; **`codigo_distinto`** (aviso) si la emparejada tiene un
`con.cod` distinto del `sigrid_cod` guardado; **`anulada_en_sigrid`** (aviso)
si la emparejada está en `NPR`.

**R13.** Una reclamación emparejada con una incidencia **no** entra en los
criterios R14–R15 frente a esa misma incidencia; sí frente a las demás.

**R13 bis.** SI dos o más reclamaciones están emparejadas con la misma
incidencia, ENTONCES **`varias_en_sigrid`** (conflicto) con todos los códigos,
y se empareja con la de código mayor.

## 4 · Los criterios de coincidencia (Q-3)

**R14.** CUANDO una incidencia **evaluable** (R16) y una reclamación tienen la
misma **unidad** (código exacto), el mismo **oficio** (código exacto) y la
misma **ubicación** (por `clave_de_ubicacion` de F-060), el sistema debe dar el
criterio **`misma_unidad_oficio_ubicacion`**. Sin código de oficio en
cualquiera de los dos lados, no se evalúa; una ubicación vacía o ausente no
casa con nada.

**R15.** *(Q-3 y N-2.)* CUANDO una incidencia evaluable y una reclamación
tienen la misma **unidad** y un **parecido** de descripción (R36) mayor o igual
que `UMBRAL_PARECIDO` (**50**, constante del dominio) con **al menos dos
palabras significativas en común** —o la misma descripción por
`normalizar_para_clave`, que es parecido 100—, comparando la descripción
vigente con `con.res`, el sistema debe dar el criterio
**`misma_unidad_descripcion_parecida`** con su `parecido`. Una descripción
vacía o sin palabras significativas no casa.

**R16.** Son **evaluables** las incidencias `nueva`, `editada`, `aprobada` y
`en_duda`; las `descartada` y las `volcada` no se evalúan por R14–R15.

**R17.** Cada par (incidencia, reclamación) con al menos un criterio debe dar
**un** hallazgo **`coincide`** con sus criterios en el orden
`misma_unidad_oficio_ubicacion`, `misma_unidad_descripcion_parecida`, el
`parecido` (o `null`) y su **severidad**: **conflicto** si la reclamación está
en `SAT` o `PTE`; **aviso** (reincidencia) si está en `TER` o `CER`, sea de la
fecha que sea. Una en `NPR` o con un código de estado que no es ninguno de los
cinco **no** da pares; las de código desconocido se cuentan
(`estados_desconocidos`).

**R18.** Por incidencia, el sistema debe devolver **como mucho 10** hallazgos
`coincide`: primero los de severidad conflicto, después por fecha de la
reclamación descendente y, a igual fecha, por código descendente; y el
**total real** (`coincidencias_total`).

**R19.** Todo lo de R10–R18 y R36 debe vivir en el **dominio puro**, sin red,
sin base y sin reloj, en **una sola función** de cruce.

## 5 · La respuesta

**R20.** CUANDO todo va bien, el sistema debe responder **200** con:

- `obra`, `leido_at_utc` (UTC con microsegundos y `+00:00`) y `criterio`:
  `{abiertas: ["SAT","PTE"], cerradas: ["TER","CER"], umbral_parecido: 50,
  tope: 500000}`;
- `reclamaciones`: cada una `{cod, estado, fecha, unidad_codigo, ubicacion,
  oficio_codigo, oficio_nombre, tipo_codigo, tipo_nombre, descripcion,
  referencia, incidencia_id, ficha}`, con `fecha` en `AAAA-MM-DD` o `null` (el
  `0` de Sigrid es nulo), `referencia` solo si empieza por `PVI-`,
  `incidencia_id` solo si está emparejada, y `ficha` con los campos de R33
  (`null` lo que no haya);
- `hallazgos`: cada uno `{tipo, severidad, incidencia_id, sigrid_cod,
  sigrid_cods, criterios, parecido}`;
- `incidencias`: por cada incidencia con algún hallazgo, indexado por
  `incidencia_id`, `{estado, unidad_codigo, ubicacion, oficio_codigo,
  descripcion, coincidencias_total}` de los **vigentes**;
- `resumen`: `{reclamaciones, por_estado, emparejadas, estados_desconocidos,
  incidencias_evaluadas, incidencias_con_conflicto, incidencias_con_aviso,
  por_tipo, por_criterio}`.

**R21.** Las reclamaciones deben ir en orden estable: fecha descendente
(`null` al final) y, a igual fecha, código descendente. Los hallazgos, por
severidad (conflicto primero), tipo, `incidencia_id` y código.

**R22.** Ninguna respuesta, tampoco las de error, debe llevar el `oid` ni el
correo de quien revisa o vuelca, el `ide` de ningún concepto ni persona, la
referencia de la obra (`obride`), ni ningún campo de Sigrid fuera de R6 y R33.
Los mensajes de error **no repiten** ninguna fila ni ningún texto de Sigrid.

**R23.** El handler debe traducir: **400** `peticion_invalida`; **409**
`bandeja_demasiado_grande`, `reclamaciones_sin_verificar` u `obra_ambigua`;
**503** sin Sigrid, sin su configuración, fuera de entorno o sin base, con el
cuerpo de error de siempre.

## 6 · Logs y tiempos

**R24.** Cada petición debe dejar **una** línea `F-065 sigrid de la bandeja`
—con 200 o con error— con la obra, el resultado (`200` o el tipo del error),
`proceso_nuevo`, los segundos totales y los de cada tramo
(`construir.sigrid`, `construir.bandeja`, `bandeja.listar`, `sigrid.leer`,
`calculo`, `serializar`), con el cronómetro de F-060 sin cambiarlo, y los
recuentos: reclamaciones, incidencias evaluadas, hallazgos por severidad y los
bytes de la respuesta. **Nunca** un texto de Sigrid o de la bandeja, un nombre,
un teléfono, un correo, una referencia, un código de reclamación ni un `oid`.

**R25.** El adaptador debe registrar la obra, las filas, si llegó al techo o
vino `truncated`, y los segundos de la lectura, **y nada más**.

## 7 · Lo que no cambia

**R26.** `GET /api/revision`, el historial, las acciones, la normalización y
las tres rutas del volcado deben quedar **sin cambios** de contrato, de número
de lecturas de Sigrid y de logs. `motivos_no_aprobable` **no gana ningún
motivo** (Q-4).

**R27.** Ninguna pieza nueva o tocada debe nombrar una ruta de la pasarela que
no sea `/api/sql/read`, ni importar las escrituras del ERP
(`infrastructure/sigrid/escrituras.py`, `graficos.py`, `volcado.py`).

**R28.** Sin variables de entorno nuevas, sin DDL, sin dependencias nuevas y
**sin caché**: cada petición lee Sigrid.

## 8 · El script de medición y los documentos

**R29.** `infra/29_reclamaciones_obra_sigrid.ps1` debe ser **solo lectura**,
ASCII sin BOM y con CRLF, pasar por `08_lectura_sigrid_comun.ps1` y lanzar **la
misma consulta** que el adaptador (texto idéntico, comprobado por un test), e
imprimir **solo recuentos y tiempos**: filas, `truncated`, **bytes de la
respuesta con todos los campos de R6 y R33** y cuántos de esos bytes son de los
campos de R33, segundos; reclamaciones por estado y por tramo de antigüedad
(< 6, 6–12, 12–24 y > 24 meses); por unidad (mínimo, mediana, máximo); sin
oficio y sin ubicación; con `PVI-`; por cada campo de R33, cuántas lo traen
relleno; los grupos (unidad, oficio, ubicación) con más de una reclamación
**dentro de Sigrid** y sus filas; y los pares de una misma unidad con parecido
≥ 40, ≥ 50 y ≥ 60 (R36, aproximada en PowerShell). **Ningún** texto, nombre,
teléfono, correo, código de reclamación ni referencia. Ningún valor de
pasarela, base ni clave en el fichero.

**R30.** `docs/ARCHITECTURE.md` (sección nueva y fila `sigrid-api` de la tabla
de acceso), `docs/INTEGRACION.md` §1 (la **cuarta lectura**) y
`azure-apps/postventa_incidencias.md` deben describir la ruta, los campos que
se sirven, que hay datos personales y dónde no van; y la fila de consumidores
de `azure-apps/sigrid_api.md` debe ganar esta lectura. En el **mismo trabajo**.

**R31.** Verificación en producción, **solo lectura**: `MANUAL (humano)`,
`tasks.md` Bloque A7, y la medición previa T-A0 (Bloque A1).

## 9 · Los datos de cada reclamación (Q-6 y N-3)

**R32.** *(Retirado el 2026-10-21 por N-3: no hay ruta de ficha; todo va en el
listado.)*

**R33.** *(N-3, aprobada el 2026-10-21.)* La `ficha` de cada reclamación en el
listado debe llevar **solo** esta lista cerrada: la descripción larga
(`rcp.tex`), el motivo (`motrcp`), la urgencia (`texurg`), la forma de
comunicación (`rcptip`), la fecha prevista de nueva visita (`fecpre`), la
solución (`solrcp`), la clase (`auxrcp`, código y nombre), los teléfonos y el
correo adicional de avisos de la reclamación (`rcp.tel`, `rcp.ele`), el
**propietario** (nombre: `con.res` de `cliide`), la **persona que reclama** y
la **persona de contacto** (de `per`: `nom`, `tel`, `tel2`, `ele`). **Nunca**:
`per.dni`, las credenciales de i-Sigrid (`per.esiglog`, `per.esigpas`,
`per.clamai`), direcciones ni observaciones de la persona, ni ningún `ide`.
Ampliar la lista es una decisión del humano.

**R34.** *(Retirado el 2026-10-21 por N-3.)*

**R35.** La respuesta de la ruta debe llevar `Cache-Control: no-store`, para
que ningún navegador ni proxy guarde lo que devuelve. El resto de rutas del
servicio no cambia.

## 10 · El parecido de dos descripciones (N-2, aprobada el 2026-10-21)

**R36.** Las **palabras significativas** de un texto deben ser: el texto
plegado (`plegar` de F-036: sin tildes, minúsculas, blancos colapsados),
partido por todo lo que no sea letra o cifra, sin las de menos de 3
caracteres, sin las de la lista cerrada `PALABRAS_VACIAS` del dominio y con la
`s` final quitada a las de 5 o más caracteres. El **parecido** de dos textos
debe ser 100 si sus `normalizar_para_clave` son iguales y no vacías; si no,
`floor(100 × |A ∩ B| / |A ∪ B|)` sobre sus palabras significativas, y 0 si
alguna no tiene ninguna. Puro y determinista: sin IA ni distancia de edición.
El umbral se puede mover con los números de T-A0.

## 11 · Los datos personales (Q-6)

**R37.** Ningún dato de una reclamación —texto, nombre, teléfono, correo,
referencia— debe **guardarse** en nuestra base ni en ningún fichero del
servicio: se leen de Sigrid en cada petición y se sirven.

**R38.** Ninguna línea de log ni traza de la ruta ni de su adaptador debe
llevar un dato de R33 ni un texto de R6: solo la obra, códigos de resultado,
recuentos, bytes y segundos.

**R39.** Los tests deben usar **solo datos inventados** («Ejemplo …», correos
`@ejemplo.invalid`, teléfonos `000 000 000`), y un test debe comprobar que
ningún fichero de tests, de `specs/` ni de `progress/` de esta ficha trae un
correo que no sea `@ejemplo.invalid`.

**R40.** Un test debe fijar que ningún mensaje de error ni ninguna excepción
que llegue al log lleva el contenido de una fila (la regla del `_mapear`
heredado), y que las filas del puerto no imprimen sus valores en su `repr`.
