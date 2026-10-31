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
>
> **Conciliación con `dev` `f7f63da` (2026-10-28, spec-author).** Dos clases de
> cambio, marcadas cada una en su sitio:
>
> - **Ajustes a la realidad del código** (no cambian ninguna decisión): R24
>   (el cronómetro de F-060 no se puede usar tal cual para la línea ni para
>   `proceso_nuevo`), R8 (dónde vive el 500.000 en la pasarela), y en
>   `design.md` la base, rutas de ficheros y piezas heredadas. Marcados
>   «*Conciliado el 2026-10-28*».
> - **Lo nuevo: la guarda del ensayo** (§12, R41–R49 y R70–R71), por la
>   decisión del humano del 2026-10-28 (C-4 de F-040: «Registrar» sincroniza
>   con Sigrid antes de registrar). **PENDIENTE DE OK del humano**: choca con
>   R26, R27 y `design.md` §13 aprobados, y con R9 y R11 de F-059; las
>   preguntas, numeradas S-1 a S-9, en `design.md` §16. R26 y R27 **no se han
>   cambiado**: llevan una nota que remite a S-1.
>
> **Enmiendas tras la review del Bloque A2 (2026-10-28).** Decisiones del humano
> sobre las lecturas 1, 2, 3, 4 y 9 de `progress/review_F-065.md` («Review del
> Bloque A2»): R12, R13, R20, R21 y R41 (esta última, **enmienda del humano a
> S-3**). Y una del líder sobre la lectura 6, que va a T5 (`tasks.md`). Marcadas
> «*Enmienda del 2026-10-28*» en su sitio.

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

> *Conciliado el 2026-10-28.* El 500.000 es el `MAX_ALLOWED_ROWS` de las App
> Settings de `func-sigridapi-dev-huyke`, la instancia que usa todo el
> ecosistema (`azure-apps/sigrid_api.md` §4.1, leído el 2026-08-18 y releído el
> 2026-09-30); el defecto del código es 1.000. La propia §4.1 avisa: «500.000
> filas es el tope que acepta la aplicación, no una recomendación… paginar
> sigue siendo obligatorio» para volúmenes grandes; de ahí la contingencia por
> trozos de `design.md` §4. Y la política de reintentos corta antes de los
> 230 s, **no** antes de los 45 s del proxy de la Static Web App
> (`SIGRID_TIMEOUT_S` 35 s × `SIGRID_REINTENTOS` 3): un mal día, quien corta es
> el proxy, con 504 y sin nada a medias (la ruta no escribe). Es lo mismo que
> ya pasa con las lecturas de F-036 y F-056; no se cambia aquí.

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

> *Enmienda del 2026-10-28 (decisiones del humano, lecturas 1 y 2 de la review
> del Bloque A2).*
>
> - **Dónde va cada código.** El código que guarda nuestra base viaja en un
>   campo propio del hallazgo, **`guardado_cod`** (R20), y **solo** en
>   `volcada_no_encontrada` y `codigo_distinto`; en los demás tipos es `null`.
>   `sigrid_cod` es siempre el `cod` de una reclamación que está en
>   `reclamaciones` de la misma respuesta, o `null`: en `volcada_no_encontrada`
>   es `null` (no hay reclamación); en `codigo_distinto` y `anulada_en_sigrid`,
>   la emparejada.
> - **`codigo_distinto` con varias.** SI la incidencia `volcada` tiene dos o
>   más reclamaciones emparejadas (R13 bis) y el código guardado **está entre
>   ellas**, ENTONCES **no** se da `codigo_distinto`: el duplicado ya lo enseña
>   `varias_en_sigrid`. SI no está entre ellas, se da, con la emparejada (la de
>   código mayor) en `sigrid_cod`.
> - **Las demás comprobaciones de R12** (`anulada_en_sigrid`) se hacen
>   **solo** contra la emparejada, la de código mayor (R13 bis): que otra de
>   las suyas esté en `NPR` no da `anulada_en_sigrid`.

**R13.** Una reclamación emparejada con una incidencia **no** entra en los
criterios R14–R15 frente a esa misma incidencia; sí frente a las demás.

> *Enmienda del 2026-10-28 (decisión del humano, lectura 3 de la review del
> Bloque A2).* Con dos o más (R13 bis), **ninguna** de las reclamaciones que
> llevan la referencia `PVI-` de una incidencia se cruza por criterios con
> ella, no solo la de código mayor: son sus propios partes, y
> `varias_en_sigrid` ya los enseña. Frente a las demás incidencias, todas
> entran en los criterios.

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
  sigrid_cods, guardado_cod, criterios, parecido}` (*enmienda del
  2026-10-28*, `guardado_cod`): `sigrid_cod`, el `cod` de una reclamación de
  `reclamaciones` o `null`; `sigrid_cods`, **siempre** códigos de Sigrid, y
  solo no vacío en `varias_en_sigrid` (todas las emparejadas, de mayor a
  menor); `guardado_cod`, el código que guarda nuestra base, solo en
  `volcada_no_encontrada` y `codigo_distinto`, `null` en los demás (R12);
- `incidencias`: por cada incidencia con algún hallazgo, indexado por
  `incidencia_id`, `{estado, unidad_codigo, ubicacion, oficio_codigo,
  descripcion, coincidencias_total}` de los **vigentes**;
- `resumen`: `{reclamaciones, por_estado, emparejadas, estados_desconocidos,
  incidencias_evaluadas, incidencias_con_conflicto, incidencias_con_aviso,
  por_tipo, por_criterio}`.

**R21.** Las reclamaciones deben ir en orden estable: fecha descendente
(`null` al final) y, a igual fecha, código descendente. Los hallazgos, por
severidad (conflicto primero), tipo, `incidencia_id` y código.

> *Enmienda del 2026-10-28 (decisión del humano, lectura 9 de la review del
> Bloque A2).* Concretado, porque es contrato con F-064:
>
> - **El tipo**, en el orden del enumerado (`coincide`, `ya_en_sigrid`,
>   `varias_en_sigrid`, `volcada_no_encontrada`, `codigo_distinto`,
>   `anulada_en_sigrid`, `referencia_desconocida`); **`incidencia_id`**
>   ascendente, con `null` delante.
> - **Los `coincide` de una misma incidencia** salen en el **orden de R18**:
>   a igual severidad, fecha de la reclamación descendente (`null` al final)
>   y, a igual fecha, código descendente. Así, tomar los `coincide` de una
>   incidencia en el orden de `hallazgos` (filtrando por `incidencia_id` y
>   `tipo`) da exactamente el orden de R18 —primero los de conflicto—, y la
>   página toma los primeros **sin reordenar**.
> - **Los demás tipos**, a igual severidad, tipo e `incidencia_id`, por
>   `sigrid_cod` ascendente (`null` delante).

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

> *Conciliado el 2026-10-28* con `interface_adapters/api/tiempos.py`, que no se
> toca (§9.3 de `design.md`):
>
> - `Cronometro.linea()` escribe **literalmente** `F-060 tiempos del
>   listado: …`; la línea de F-065 la compone el borde con `tramos()`,
>   `total()` y `calculo()`, con el mismo formato de números (tres decimales).
> - `calculo()` es «el tramo `aplicacion` menos lo que sumaron los puertos
>   medidos»: la lista de tramos de R24 gana **`aplicacion`** (que envuelve la
>   llamada a `mirar_sigrid`), y `calculo` sale de él.
> - `es_primera_peticion()` es **un solo indicador por proceso, el del
>   listado**: si el borde de F-065 lo llamara, se lo comería y la línea de
>   F-060 diría `proceso_nuevo=False` cuando no lo es, que es cambiar sus logs
>   (R26). `proceso_nuevo` de F-065 sale de un indicador **propio** del módulo
>   del borde, con el mismo patrón (un `bool` y un `threading.Lock`), y la línea
>   lleva además `segundos_de_proceso` (`segundos_de_proceso()`, que no consume
>   nada). Un test fija que pedir esta ruta no cambia el `proceso_nuevo` del
>   siguiente listado.

**R25.** El adaptador debe registrar la obra, las filas, si llegó al techo o
vino `truncated`, y los segundos de la lectura, **y nada más**.

## 7 · Lo que no cambia

**R26.** `GET /api/revision`, el historial, las acciones, la normalización y
las tres rutas del volcado deben quedar **sin cambios** de contrato, de número
de lecturas de Sigrid y de logs. `motivos_no_aprobable` **no gana ningún
motivo** (Q-4).

> *Nota del 2026-10-28 (no cambia el texto aprobado).* La guarda del ensayo
> (§12) cambia `POST /api/volcado/ensayo`: una clave opcional en el cuerpo,
> una lectura más de Sigrid, dos motivos de exclusión y un bloque más en la
> respuesta. Si el humano la aprueba, R26 se lee «…y **dos** de las tres rutas
> del volcado (el panel y `volcar`) sin cambios; el ensayo cambia exactamente
> lo de R43–R48». Pregunta **S-1** de `design.md` §16.

**R27.** Ninguna pieza nueva o tocada debe nombrar una ruta de la pasarela que
no sea `/api/sql/read`, ni importar las escrituras del ERP
(`infrastructure/sigrid/escrituras.py`, `graficos.py`, `volcado.py`).

> *Nota del 2026-10-28 (no cambia el texto aprobado).* Con la guarda, se
> tocan piezas de F-059 que **ya** construyen el ensayador
> (`interface_adapters/api/volcado.py` importa `construir_ensayador`, que
> compone el adaptador de `partes-reclamacion`). Si el humano la aprueba, R27
> se lee «ninguna pieza **nueva** de F-065…; las de F-059 que se tocan
> conservan sus importaciones y no ganan ninguna». S-1.

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

## 12 · La sincronización antes de registrar y la guarda del ensayo (nuevo, 2026-10-28, PENDIENTE DE OK)

> **Origen**: decisión del humano del 2026-10-28 (C-4 de la conciliación de
> F-040): el panel de volcado tendrá un botón **«Registrar»** que **sincroniza
> con Sigrid antes de registrar**, con la filosofía de `dedicacion`
> (`azure-apps/dedicacion.md`: antes de escribir se lee lo que ya hay en Sigrid
> y nunca se duplica; un `truncated` es error y no se escribe nada). El botón
> hace, en este orden: (1) leer las reclamaciones de la obra y cruzarlas con
> las aprobadas —esta ficha—; (2) enseñar qué va, qué ya existe y qué choca,
> con el recuento por unidad; (3) solo entonces ensayar y volcar (F-059). Para
> que la regla la garantice el **backend** y no el front, el **ensayo** de
> F-059 vuelve a mirar Sigrid y aplica la misma regla.
>
> Numeración: R41–R49 y R70–R71 (R50–R69 son de F-064). **Todo este bloque
> está pendiente de OK del humano**: las decisiones que encierra son S-1 a S-9
> de `design.md` §16, cada una con la recomendación con la que está escrito.

**R41.** *(S-2, S-3.)* El sistema debe dar a cada incidencia **candidata al
volcado** (`aprobada` o `en_duda`, `es_candidata` de F-056) **un** veredicto,
calculado en el **dominio puro** por la **misma** función en la ruta de F-065 y
en el ensayo, a partir de **todos** sus pares (no solo los 10 de R18), con esta
precedencia:

1. **`se_enlaza`** si tiene una reclamación emparejada por `PVI-` (hallazgo
   `ya_en_sigrid` o `varias_en_sigrid`): mandarla **no puede crear** otro
   parte —la pasarela la devuelve `idempotente` (misma UPV) o la rechaza
   `referencia_en_conflicto` (otra UPV, o más de una)—, y el `idempotente` del
   ensayo la deja `volcada` (R13 y R27 de F-059);
2. **`ya_existe`** si tiene un `coincide` con **los dos** criterios
   (`misma_unidad_oficio_ubicacion` **y** `misma_unidad_descripcion_parecida`)
   con una reclamación **abierta** (`SAT`, `PTE`);
3. **`choca`** si tiene algún otro `coincide` de severidad **conflicto**;
4. **`va`** en todos los demás casos, también con avisos (reincidencias en
   `TER`/`CER`).

Cada veredicto lleva los **códigos** de las reclamaciones que lo deciden, en el
orden de R18: la emparejada en `se_enlaza`; las de los dos criterios en
`ya_existe`; **todas** las de conflicto en `choca`; ninguno en `va`.

> *Enmienda del 2026-10-28: **enmienda del humano a S-3*** (lectura 4 de la
> review del Bloque A2). SI la reclamación emparejada de una candidata —la de
> código mayor, R13 bis— está en **`NPR`** (anulada en Sigrid), ENTONCES el
> veredicto es **`choca`**, no `se_enlaza`: mandarla la dejaría `volcada`
> enlazada a un parte anulado (el `idempotente` de la pasarela), y eso exige
> la **confirmación explícita** en el ensayo, como el resto de `choca` (R45:
> sin ella, `conflicto_sin_confirmar`). Va **antes** de la regla 1 en la
> precedencia: una candidata emparejada con una `NPR` es `choca` aunque
> también tenga un `ya_existe` o un `choca` por criterios. Sus códigos: **solo
> el de la emparejada**, porque es la que decide lo que hará la pasarela (no
> puede crear otro parte, así que los `coincide` no cambian nada). Que otra de
> las suyas (no la mayor) esté en `NPR` no cambia el veredicto, como en R12.
> La regla 1 se lee entonces «`se_enlaza` si tiene una reclamación emparejada
> por `PVI-` **que no está en `NPR`**».
>
> *Enmienda del 2026-10-29: **decisión del humano sobre L-3*** (review de la
> primera mitad del Bloque A4 bis). La regla 0 vale igual SI el estado de la
> emparejada **no es ninguno de los cinco conocidos o viene vacío** (`None`):
> el veredicto es **`choca`**, con el mismo código (solo el de la emparejada) y
> la misma confirmación explícita. Si no se sabe en qué estado está el parte,
> lo mira una persona. La regla 1 se lee entonces «`se_enlaza` si tiene una
> reclamación emparejada por `PVI-` **en PTE, SAT, TER o CER**».

**R42.** *(S-9.)* CUANDO la ruta de R1 responde 200, la respuesta debe llevar
además un bloque **`volcado`** —aditivo: R20 no pierde ni cambia nada—:
`{candidatas, por_veredicto: {va, se_enlaza, ya_existe, choca}, por_unidad:
{<unidad_codigo>: {va, se_enlaza, ya_existe, choca}}, veredictos:
[{incidencia_id, unidad_codigo, estado, veredicto, sigrid_cods}]}`, con las
candidatas de la obra en el orden de R25 de F-056 y las unidades por código.
Es lo que enseña el paso (2) del botón «Registrar» de F-040.

**R43.** *(S-1, S-4.)* El cuerpo de `POST /api/volcado/ensayo` debe admitir,
además de las cuatro claves de R9 de F-059, **una clave opcional**
`conflictos_confirmados`: una lista de como mucho `N` objetos con
**exactamente** `incidencia_id` (un UUID que está en `incidencias`, sin
repetir) y `sigrid_cods` (lista de 1 a 50 códigos **distintos** con la forma
`RS<aa>.<mm>/<4 cifras>`, `PATRON_COD_PARTE` de F-059). SI no cumple eso,
ENTONCES **400** `peticion_invalida` antes de construir ningún adaptador y sin
repetir nada de lo recibido. Sin la clave, es una lista vacía. El resto de R9
no cambia (también: `commit` y `confirmado` siguen siendo 400).

**R44.** *(S-5.)* CUANDO, tras la selección de R11 de F-059, el ensayo tiene
algo que mandar, el sistema debe hacer **una** lectura de Sigrid de las
reclamaciones de la obra **solo de las unidades de lo que se va a mandar**
(como mucho `N` códigos de unidad, todos por marcador `?`), con las columnas de
R6 **sin** los campos de R33 (la guarda no lee ni un dato personal), el techo
de R8 y la comprobación de `truncated` y de obra única de R8 y R9; cruzar con
R10–R17 y R36; y dar el veredicto de R41. **Después** de la selección y
**antes** del login de Sigrid (F-009) y del lote. Si la selección no deja nada
que mandar, **no** lee Sigrid (como hoy no hay login).

**R45.** *(S-2, S-3, S-4.)* Con el veredicto de R44, el ensayo debe:

- **excluir sin mandarla**, con el motivo nuevo **`duplicada_en_sigrid`** y el
  primer código de su veredicto en `sigrid_cod`, toda incidencia `ya_existe`;
- **excluir sin mandarla**, con el motivo nuevo **`conflicto_sin_confirmar`** y
  el primer código **no confirmado** en `sigrid_cod`, toda incidencia `choca`
  cuyos códigos de conflicto **no estén todos** en su entrada de
  `conflictos_confirmados` (una reclamación que choca y que apareció después de
  confirmar exige confirmarla también);
- **mandar** las `choca` con todos sus códigos confirmados, las `se_enlaza` y
  las `va`, en el orden pedido, como hoy.

Una confirmación de una incidencia que ya no choca se ignora y se cuenta. SI
tras la guarda no queda nada que mandar, ENTONCES la respuesta de «nada que
mandar» de F-059 (`ensayo_id: null`), **sin** login ni lote.

> *Enmienda del 2026-10-28 (consecuencia de la enmienda a S-3, R41).* «Sus
> códigos de conflicto» son **los códigos de su veredicto**: en una `choca`
> por una emparejada en `NPR`, el de esa emparejada. Confirmarlo es confirmar
> que se enlace con el parte anulado; sin confirmarlo, sale
> `conflicto_sin_confirmar` con ese código en `sigrid_cod`.

**R46.** *(S-8.)* SI la lectura de la guarda falla —la pasarela no responde,
responde mal formado o fuera de entorno— ENTONCES **503**
`sigrid_no_disponible`; SI viene con `truncated` o llega al techo, **409**
`reclamaciones_sin_verificar` con el número de filas; SI son filas de más de
una obra, **409** `obra_ambigua`. En los tres casos **no se ensaya**: ni login,
ni lote, ni ensayo guardado, ni nada a medias. Sin interruptor que apague la
guarda (R28: sin variables nuevas).

**R47.** La respuesta 200 del ensayo debe llevar además un bloque **`sigrid`**
—aditivo: las claves de R12 de F-059 no cambian, `resumen` tampoco y las
`excluidas` conservan su forma `{incidencia_id, motivo, sigrid_cod}`—:
`{leido_at_utc, reclamaciones_leidas, veredictos: [{incidencia_id, veredicto,
sigrid_cods, confirmada}]}` por cada incidencia que pasó por la guarda, en el
orden pedido; y `sigrid: null` cuando la guarda no leyó (R44).

**R48.** El ensayo debe dejar **una** línea `F-065 guarda del ensayo` por
lectura, con la obra, la `llamada_id` (el `ensayo_id`, o `-` si no se guardó),
las unidades leídas (**cuántas**, no cuáles), las reclamaciones leídas, cuántas
incidencias por veredicto, cuántas excluidas por cada motivo nuevo, cuántas
mandadas con conflicto confirmado, cuántas confirmaciones sobrantes y los
segundos de la lectura; y una línea por incidencia mandada con conflicto
confirmado con su `incidencia_id` y **cuántos** códigos confirmó. **Nunca** un
código de reclamación, un texto de Sigrid ni nada de R33 (R38).

**R49.** *(S-6, S-7.)* `POST /api/volcado/volcar` y `GET /api/volcado` **no
cambian** —ni contrato, ni lecturas de Sigrid, ni logs—: el volcado solo manda
lo que un ensayo vigente (≤ 30 min, R17 de F-059) dio `previsto`, así que lo
que la guarda excluye no puede volcarse. La confirmación **no se guarda** en la
base (sin DDL): consta en el log de R48. Un test debe fijar, con fixtures, que
el veredicto de una incidencia es **el mismo** con la lectura de toda la obra
(R5) y con la de sus unidades (R44), salvo el caso escrito de una referencia
`PVI-` en otra unidad (que la pasarela rechaza igualmente).

**R70.** *(Medición, S-5.)* `infra/29_reclamaciones_obra_sigrid.ps1` debe
admitir `-Unidades` (una lista de códigos) y lanzar entonces **la misma
consulta** que la lectura de la guarda (texto idéntico para 1 y para 5
unidades, comprobado por un test), con las reglas de R29: solo lectura, solo
recuentos, bytes y segundos.

**R71.** *(Medición, MANUAL.)* Antes del bloque de la guarda, el humano mide en
solo lectura (`tasks.md`, T-A0 bis): el tiempo y los bytes de la lectura de
toda la 0677 (R5) y de la de una y de cinco unidades (R44), entre ellas la
VILLA 15; y, tras publicar, la duración del ensayo con la guarda en Application
Insights. Si la lectura de la obra pasa de ≈ 10 s, o la de la guarda de ≈ 3 s,
se vuelve al humano antes de seguir.
