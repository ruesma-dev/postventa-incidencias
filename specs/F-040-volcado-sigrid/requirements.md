<!-- specs/F-040-volcado-sigrid/requirements.md -->
# F-040 · Volcar a Sigrid las incidencias aprobadas (el panel de volcado) — Requisitos

> **Aprobado por el humano el 2026-10-07**, con D-1 a D-14 como se
> recomendaban y las respuestas Q-1 a Q-8 (todas en
> `specs/F-059-volcado-sigrid-backend/design.md` §20; las que tocan a esta
> ficha, en `design.md` §6).
>
> **Conciliado con `dev` el 2026-10-27** (spec-author, rama nueva
> `feature/F-040-volcado-sigrid` desde `dev` `f7f63da`): contra el código de
> F-059 tal como se cerró y desplegó, contra `bandeja.html` y `js/revision.js`
> de F-038 tal como están publicados y contra F-060. Lo que es solo ajuste a la
> realidad del código está corregido aquí mismo y resumido en el §4; lo que
> tocaría una decisión aprobada o el alcance **no** se ha cambiado: son las
> preguntas **C-1 a C-6** de `progress/spec_F-040.md` («Conciliación
> 2026-10-27»).
>
> **Respuestas del humano a C-1…C-6 aplicadas el 2026-10-28** (§5): el botón
> **«Registrar»** sincroniza con Sigrid antes de ensayar (C-4, R60–R62), lo
> que hace a F-040 **depender de F-065**, que va antes; recuento por unidad en
> el ensayo y en la confirmación (C-3, R61, R52); el volcado de la VILLA 15
> no es tarea de la ficha (C-2); los Bloques 1 y 2 no esperan a F-038 y el
> Bloque 3 sí (C-1); aprobar en bloque, fuera (C-5); T5 en la 0626 (C-6).
>
> **Conciliado con el contrato implementado de F-065 el 2026-10-31** (T0,
> spec-author, base fija `f97ec6e`, que trae `dev` `7cc0bbb` con F-065 `done`
> y desplegada desde `ed590bd`): R60–R62, el glosario y R54 dicen ya la ruta,
> la forma y los errores reales de la sincronización y de la guarda del
> ensayo, con su fichero y línea en el §6. Lo que tocaría una decisión
> aprobada se preguntó como **P-1 a P-3** (`progress/spec_F-040.md`,
> «Conciliación con F-065, 2026-10-31»); **respuesta del humano 2026-10-31**:
> las tres como se recomendaron, ya aplicadas y marcadas «(P-n, respuesta del
> humano 2026-10-31)».
>
> **Partida por D-1 (decisión del humano del 2026-10-07).** El backend —ensayo,
> volcado, tabla `volcados_sigrid`, estados `volcada` y `en_duda`, ventana
> `VOLCADO_HABILITADO`, verificación de la escritura en producción— es la
> ficha **F-059** (`specs/F-059-volcado-sigrid-backend/`), **`done`**:
> desplegada el 2026-10-17 y verificada en producción el 2026-10-19 (obra 0626,
> un parte, anulado después). **Esta ficha es el front**: el panel de volcado
> en `bandeja.html` y el cierre de los restos de F-040 en el portal.
> *(Conciliado 2026-10-27: F-038 está mergeada en `dev` y `bandeja.html`
> publicada, pero la ficha sigue `blocked` a la espera de su T7 manual.
> Decidido el 2026-10-28 (C-1): los Bloques 1 y 2 no la esperan; el Bloque 3,
> el cierre, espera a F-038 `done`.)*
>
> **Dependía de F-065** (decisión del humano del 2026-10-28, C-4): el
> backend que lee las reclamaciones de la obra en Sigrid y las cruza con la
> bandeja (`specs/F-065-revision-sigrid-backend/`) está **`done`**, mergeado
> en `dev` (`7cc0bbb`) y desplegado el 2026-10-31 desde `ed590bd`; la rama de
> F-040 lo trae en su base fija, `f97ec6e` (`progress/impl_F-040.md`).
>
> Los números de requisito vienen de la spec conjunta: R1–R43 son de F-059;
> los de esta ficha son **R50–R59**. Rama `feature/F-040-volcado-sigrid`.
> Rigor **`critico`**: es el botón que escribe en el ERP de producción.

## 0 · De dónde sale

La ficha pide que lo aprobado en la bandeja se cree en Sigrid **con dry-run
previo y confirmación**, en lote, que **su número vuelva a la bandeja** y que
**reintentar no duplique**. F-059 da las tres rutas que lo hacen
(`GET /api/volcado`, `POST /api/volcado/ensayo`, `POST /api/volcado/volcar`;
el contrato **implementado** está en `design.md` §1) y los estados nuevos en
`GET /api/revision` (su R4). Esta ficha es lo que una persona de Posventa
toca: ver qué se crearía, confirmar, volcar, ver qué pasó y reintentar.

**Sincronizar antes de registrar (decisión del humano del 2026-10-28, C-4).**
Como en `dedicacion` (`azure-apps/dedicacion.md`: leer lo que ya hay en
Sigrid y no duplicar), el panel no ensaya a ciegas: su botón **«Registrar»**
primero trae las reclamaciones de la obra desde Sigrid y las cruza con las
aprobadas (el backend de **F-065**), enseña qué va, qué ya existe y qué
choca, y **solo entonces** ensaya y vuelca de 5 en 5. El volcado de F-059
solo reconoce sus propios partes (`PVI-`); lo que Posventa dio de alta a mano
en Sigrid lo ve F-065.

**El volumen real (conciliado 2026-10-27).** El primer uso previsto es la
VILLA 15 de la 0677: unas **285** incidencias importadas por Excel, que con
`partes_por_llamada` = 5 son **57 trozos**, 57 ensayos y 57 volcados de uno en
uno. Lo medido en la verificación de F-059 (2026-10-19, un parte): ensayo de
1,2 s a 5,8 s, volcado 1,8 s, y un primer ensayo tras abrir la ventana de
**35 s** (arranque en frío de `sigrid-api`). Con esas cifras la obra entera
cabe en los 30 minutos de vida de un ensayo, pero no con holgura si la
pasarela va lenta; los requisitos de abajo (R51 a R53) dicen qué pasa cuando
no cabe. El volcado real de la VILLA 15 lo hará el humano cuando el panel
esté operativo: **no es una tarea de esta ficha** (C-2, 2026-10-28).

## 0.1 · Glosario

Los de F-059 (candidata, referencia, ensayo, volcado, llamada, en duda), más:

- **Trozo**: grupo de como mucho `partes_por_llamada` incidencias (el valor
  que devuelve `GET /api/volcado`, hoy 5); un ensayo y un volcado por trozo.
- **Ensayo de la obra**: el conjunto de los ensayos de todos los trozos,
  enseñados juntos.
- **Sincronización** *(2026-10-28; contrato de F-065, 2026-10-31)*:
  `GET /api/revision/sigrid?obra=` (F-065), el primer paso de «Registrar»:
  las reclamaciones de la obra en Sigrid cruzadas con la bandeja y, en su
  bloque `volcado`, el **veredicto** de cada candidata (`aprobada` o
  `en_duda`). Solo lee.
- **Va / ya existe / choca** *(2026-10-28; conciliado 2026-10-31)*: cómo queda
  cada candidata tras la sincronización, según su `veredicto` de F-065
  (`domain/models/sigrid_bandeja.py` `Veredicto`, l. 127–137, y su precedencia
  en `_veredicto`, l. 697–713):
  - **Va**: veredicto `va` (nada abierto en Sigrid que la reclame; también con
    avisos de reincidencias en `TER`/`CER`), **y** `se_enlaza` (Sigrid ya tiene
    **su** parte, con su referencia `PVI-`, en `PTE`, `SAT`, `TER` o `CER`: la
    pasarela no crea otro y el ensayo la devuelve `idempotente`), que se
    enseña dentro de «va» con su código y la marca «se enlaza con RS…» *(P-1, respuesta del humano 2026-10-31)*, sumada al recuento de va. Se
    ensaya.
  - **Ya existe**: veredicto `ya_existe` (una reclamación abierta, `SAT` o
    `PTE`, casa con los dos criterios de F-065). Se excluye, sin salida.
  - **Choca**: veredicto `choca` (alguna otra coincidencia de conflicto con una
    abierta, **o** su propio parte `PVI-` está anulado en Sigrid —`NPR`— o en
    un estado desconocido). Solo se ensaya con un segundo clic.
- **Sin respuesta del servicio** *(conciliado 2026-10-27)*: un `ErrorApi`
  con `http` nulo de `js/api.js` —red caída o la petición abortada a los 40 s
  (`TIMEOUT_PETICION_MS`)—. En un volcado **no dice** que no se haya escrito.

## 1 · El panel (D-2)

- **R50.** `bandeja.html` (de F-038) debe tener un panel **«Volcado a
  Sigrid»** con su lógica en un fichero propio, `js/volcado.js`, montado
  **dentro del único `x-data="appRevision()"`** de la página (la guardia R70 de
  F-035 exige un solo elemento con `x-data`; conciliado 2026-10-27). CUANDO la
  bandeja carga una obra, el panel debe pedir `GET /api/volcado` (solo lee) y
  enseñar aprobadas, en duda y volcadas, cuántas candidatas hay y en cuántos
  trozos irán, y el aviso de que el ensayo no crea nada. Su acción de entrada
  es **un** botón, **«Registrar»** (R60) *(2026-10-28: sustituye a «Ver qué se
  crearía en Sigrid» como primer clic; el ensayo es su tercer paso)*.

### 1.1 · Registrar: sincronizar, enseñar, y solo entonces ensayar (C-4, 2026-10-28)

- **R60.** CUANDO se pulsa **«Registrar»**, el panel debe, **en este orden**
  y sin saltarse ninguno: (1) pedir `GET /api/revision/sigrid?obra=` (F-065;
  `function_app.py` l. 2074–2119) **una vez**, sin reintento automático
  (`sinReintentos`: lo repite la persona con otro «Registrar»); (2) enseñar el
  resultado (R61) y esperar; (3) solo con un clic más, ensayar y volcar como
  dicen R51–R53. SI la sincronización no responde 200 o queda sin respuesta
  del servicio, ENTONCES el panel debe parar ahí: **no** ensaya ni deja
  ensayar, y lo dice según el error (`design.md` §3.2): 400
  `peticion_invalida`; 409 `bandeja_demasiado_grande` (con `total`); 409
  `reclamaciones_sin_verificar` (con `filas`: la lectura llegó al techo o vino
  `truncated`, y F-065 no cruza nada); 409 `obra_ambigua`; **503 sin
  `codigo`** (Sigrid, su configuración o la base: `_sin_sigrid_o_sin_base`,
  l. 1344–1361, solo trae `error`).
- **R61.** Tras la sincronización, el panel debe enseñar cada candidata del
  bloque `volcado.veredictos` de la respuesta
  (`interface_adapters/api/sigrid_bandeja.py` `_volcado`, l. 324–347:
  `{incidencia_id, unidad_codigo, estado, veredicto, sigrid_cods}`, en el
  orden de la bandeja) en uno de tres grupos —**va** (con `se_enlaza` marcado
  y su código, *P-1, respuesta del humano 2026-10-31*), **ya existe** (con sus `sigrid_cods`) y **choca** (con
  cada reclamación de sus `sigrid_cods`: su estado, unidad, ubicación, oficio
  y descripción, de `reclamaciones` de la misma respuesta, y por qué choca:
  «su parte está anulado en Sigrid» si es la emparejada de la incidencia
  —`reclamaciones[].incidencia_id`— o, si no, los `criterios` y el `parecido`
  de su `hallazgo` `coincide`)— y el **recuento por unidad** de cada grupo
  (C-3), de `volcado.por_unidad` (por `unidad_codigo` **vigente**, con los
  cuatro veredictos; va = `va` + `se_enlaza`), con el nombre de la unidad del
  `catalogo` de `GET /api/revision` (sin nombre, el código). El panel **no**
  enseña la `ficha` (datos personales, R33 de F-065) y no guarda la respuesta
  fuera de la memoria de la página (R55).
- **R62.** Lo que **ya existe** en Sigrid se excluye: no se ensaya ni se
  vuelca, y no hay botón que lo incluya. Lo que **choca** no se ensaya salvo
  que la persona lo incluya con un **segundo clic** explícito **por
  incidencia**, con sus reclamaciones a la vista y sin «todas las de la unidad» *(P-2, respuesta del humano 2026-10-31)*; sin él, se queda fuera y sale como tal en el
  resultado. En una que choca porque su parte está anulado (`NPR`), el texto
  del segundo clic debe decir que incluirla **la enlaza con el parte anulado**
  y no crea otro (R41 y R45 de F-065, enmienda a S-3). El ensayo lleva lo
  incluido en la clave opcional `conflictos_confirmados: [{incidencia_id,
  sigrid_cods}]` (`interface_adapters/api/volcado.py` l. 461–504), con
  **todos** los `sigrid_cods` de su veredicto de la sincronización y solo las
  incidencias de ese trozo. El backend aplica la misma guarda en el ensayo
  (`application/pipelines/guarda_sigrid.py` l. 131–153), que **relee Sigrid**
  en cada trozo, así que el panel no es la única defensa y la sincronización
  no caduca: SI el ensayo excluye una incidencia con `duplicada_en_sigrid` o
  con `conflicto_sin_confirmar` —también la que en la sincronización iba, o
  una incluida cuya `sigrid_cod` no estaba entre los códigos confirmados (una
  reclamación nueva)—, ENTONCES el panel debe enseñarla en las excluidas con
  su texto y ofrecer «Volver a registrar».

### 1.2 · Ensayo y volcado

- **R51.** CUANDO, tras la sincronización (R60), se pide el ensayo, el panel
  debe partir **las que van** (y las que chocan incluidas con su segundo
  clic), **tal como las nombra la sincronización** *(conciliado 2026-10-31:
  una candidata que `GET /api/volcado` trae y la sincronización no —aprobada
  después de sincronizar— no se ensaya: el panel la cuenta aparte y pide
  «Volver a registrar»)*, en trozos de `partes_por_llamada`, pedir los ensayos
  **de uno en uno** con su progreso («trozo k de M») y enseñar, juntos, cada
  parte con su unidad, oficio y proveedor (el nombre del `catalogo` de la
  respuesta de `GET /api/revision` que la página ya tiene; sin nombre, el
  código del `envio`), ubicación, descripción, tipo (`0002` PRIMER LISTADO
  POSTVENTA) y estado (`previsto` → `Se crearía`; `idempotente` → `Ya estaba
  creado`; `rechazado` → `No se crea` con el texto de su motivo;
  `no_procesado` → `No se llegó a intentar` con el texto de su motivo), y las
  excluidas con el texto de su motivo, más el **recuento por unidad** de lo
  que se crearía (C-3, 2026-10-28). Un ensayo que responde 200 sin
  `ensayo_id` (nada que mandar en ese trozo) es un trozo sin previstos, no un
  fallo. SI un ensayo no responde 200 —o queda sin respuesta del servicio—,
  ENTONCES el panel debe parar la serie (no pide los trozos siguientes),
  decir por qué y no habilitar el volcado.
- **R52.** **«Volcar N partes a Sigrid»** (N = la suma de los `previsto` de
  todos los ensayos) solo se habilita con al menos un `previsto`, con todos
  los ensayos en 200, con la caducidad más temprana sin alcanzar (cuenta atrás
  visible) y sin ninguna petición en vuelo, y tras una **confirmación
  explícita** (**D-12**: segundo clic y teclear el número de partes), cuyo
  texto dice el **recuento por unidad** de lo que se va a crear (C-3,
  2026-10-28: «Se van a crear 285 partes: 280 de VILLA 15 y 5 de VILLA 14»).
  Manda un
  volcado por cada ensayo **que tenga algún `previsto`**, con su `ensayo_id` y
  solo sus `previsto`, cada uno con la `revision_id` de su parte del ensayo; un
  ensayo sin previstos no se manda (el backend rechaza una lista vacía con
  400). `confirmado: true` aparece en **una sola** función de `js/volcado.js`.
- **R53.** Los volcados se piden **de uno en uno**, en el orden de los
  ensayos, y:
  1. ANTES de mandar cada trozo, SI su ensayo ya ha caducado (su
     `caduca_at_utc`), ENTONCES el panel debe parar sin mandarlo y decir que
     hay que volver a registrar lo que queda *(conciliado 2026-10-27: con 57
     trozos, el trozo 1 puede caducar a mitad del volcado)*.
  2. SI un volcado no responde 200, o queda **sin respuesta del servicio**, o
     responde 200 con algún parte `sin_respuesta` (`resumen.sin_respuesta` >
     0), ENTONCES el panel debe **parar** (no manda los siguientes), enseñar
     qué quedó creado, qué en duda y qué sin mandar, y **no reintentar solo**:
     ni el panel ni `js/api.js` (las peticiones de ensayo y de volcado van
     `sinReintentos`).
  3. El texto de la parada sale del `codigo` del error (la tabla de
     `design.md` §3.2): con un 503 `volcado_deshabilitado` dice que la ventana
     del volcado está cerrada; con un 502 `volcado_sin_respuesta`, que las
     incidencias de su lista `en_duda` quedan en duda y que volver a ensayar y
     volcar es seguro; sin respuesta del servicio, que no se sabe qué pasó con
     ese trozo hasta volver a leer.
  4. El resultado acumulado enseña creados (con su `RS…`), ya creados,
     rechazados y no procesados con su motivo, excluidas con su motivo, en
     duda, sin mandar, y los **avisos** de posible duplicado de la respuesta
     (las dos referencias de Sigrid, F-059 R26).
  5. AL terminar o parar —y tras una serie de ensayos con algún
     `idempotente`, que ya deja la incidencia `volcada`—, el panel debe volver
     a pedir `GET /api/volcado` y la primera página de la bandeja.
  6. **«Volver a registrar»** es el único reintento: lo pulsa una persona y
     repite R60 **desde la sincronización** con las candidatas que devuelve el
     panel en ese momento (que ya no incluyen las volcadas y sí las en duda,
     F-059 R27). Es como se reanuda un volcado parado. *(2026-10-28: antes
     «Volver a ensayar»; con C-4 no hay ensayo sin sincronización previa, y
     lo recién creado tiene que salir como «ya existe».)*
- **R54.** *(Conciliado 2026-10-27: la parte de la lista ya está en `dev`.)*
  La lista de la bandeja —`volcada` con su código de Sigrid, quién y cuándo;
  `en_duda` con su línea; los filtros `volcada` y `en_duda`; un texto para
  cada código de parte y de lote de §8.9— la cumple ya **F-038 R21**
  (`js/revision.js`: `lineaDeVolcado`, `textoMotivoVolcado`), por su Q-6
  aprobada el 2026-10-20; esta ficha no la rehace. Lo que queda aquí: el panel
  debe tener texto en castellano para **cada** motivo de exclusión de F-059
  (`no_es_de_la_bandeja`, `de_otra_obra`, `no_es_candidata`, `ya_volcada`,
  `huella_no_coincide`, `fuera_del_ensayo`, `revision_desactualizada`) y de
  la guarda de F-065 (`duplicada_en_sigrid`, `conflicto_sin_confirmar`:
  `domain/models/volcado.py` `MotivoExclusion`, l. 188–204), para
  cada causa de `ensayo_no_valido` (`no_existe`, `de_otra_obra`,
  `de_otra_persona`, `caducado`), para cada `codigo` de error de las tres
  rutas —con los tres de la guarda del ensayo: `sigrid_no_disponible`,
  `reclamaciones_sin_verificar` y `obra_ambigua` (`function_app.py`
  `CODIGOS_DEL_VOLCADO`, l. 1892–1895)— y de la sincronización (R60), y para
  el 503 de la sincronización, que llega **sin** `codigo`; los códigos de §8.9 los traduce `Revision.textoMotivoVolcado`, sin
  copiar su tabla. Un código desconocido sale tal cual.
- **R55.** Ni el correo ni el `oid` van a `console` ni al almacenamiento del
  navegador; tampoco nada de la respuesta de la sincronización, que lleva
  datos personales de clientes y viene con `Cache-Control: no-store` (R35 de
  F-065) *(conciliado 2026-10-31)*. MIENTRAS haya una serie de ensayos o de volcados en marcha, salir
  de la página debe preguntar; lo hace la **misma** guarda de salida de
  `bandeja.html` (F-038 R13), ampliada, no una segunda.
- **R56.** Nada sale sin un clic: cargar el panel solo lee; sincronizar,
  ensayar y volcar solo desde `@click`; con una petición en vuelo, ningún
  botón de «Registrar», de ensayo ni de volcado.
- **R59.** Tras un volcado con algún `creado`, el panel debe decir que **los
  partes quedan en SAT en Sigrid y que Posventa tiene que pasarlos a PTE a
  mano** (Q-3), que es cuando Sigrid avisa al industrial.

## 2 · El cierre de la ficha en el portal

- **R57.** En **un solo commit** que **también** pone F-040 en `done` (como D-11
  de F-038): fuera los restos de F-040 de la maqueta —el panel de
  `index.html#/bandeja`, lo de `MaquetaDatos.volcado` que solo servía a ese
  panel (`ficha`, `dryRun`, `hecho`, `pendientes`, `catalogos.estados`), las
  entradas `bandeja.verVolcado`, `bandeja.volcar` y `bandeja.reintentarVolcado`
  de `PLACEHOLDERS` y lo que solo les servía (`estadoVolcado`,
  `resumenVolcado` y sus funciones de `js/portal.js`)— y en su lugar un enlace
  «Volcar a Sigrid» a `bandeja.html`. *(Conciliado 2026-10-27: los catálogos
  `tipos`, `formas` y `oficios` de `MaquetaDatos.volcado` **se quedan**: los
  usan `tipo()`, `forma()` y `oficio()` de `js/portal_app.js` en las secciones
  de incidencias de la maqueta; se mudan fuera de `volcado`, sin ficha.)* Las
  guardias de F-035 siguen en verde; F-039 y F-043 conservan sus restos. Este
  commit va **después** de que F-038 esté `done` (C-1, 2026-10-28).
- **R58.** `services/postventa-front/README.md` y `docs/ARCHITECTURE.md`
  cuentan el panel de volcado, y `azure-apps/postventa_incidencias.md` deja de
  hablar de F-040 en futuro *(conciliado 2026-10-27: regla de mantenimiento
  de `azure-apps/`; el documento cita F-040 como pendiente en tres sitios)*.

## 3 · Fuera de alcance

| Qué | Dónde |
|---|---|
| Ensayo, volcado, estados, tabla, ventana, verificación de la escritura | **F-059** (`done`) |
| La presentación de `volcada` y `en_duda` en la lista | **F-038 R21** (ya en `dev`) |
| Pasar el parte a PTE | **Posventa, a mano en Sigrid** (Q-3); el panel solo lo recuerda (R59) |
| Abrir o cerrar la ventana del volcado | `infra/27_ventana_volcado.ps1` (F-059), no el front |
| Proponer el industrial | **F-039** |
| Aprobar en bloque | **F-043** (C-5, 2026-10-28) |
| Filtrar el volcado por unidad | Nadie: el panel vuelca la obra y enseña el recuento por unidad (C-3, R61, R52) |
| Leer las reclamaciones de la obra en Sigrid y cruzarlas con la bandeja; la guarda del ensayo | **F-065**, que va antes (C-4); el panel lo consume (R60–R62) |
| Los conflictos con Sigrid en la lista de la bandeja | **F-064** |
| El volcado real de la VILLA 15 de la 0677 | **El humano**, cuando el panel esté operativo; no es tarea de la ficha (C-2) |
| El ajuste de `N` | Más adelante (Q-8) |
| Recrear un parte anulado | Nadie (Q-5) |

## 4 · Conciliación 2026-10-27 (qué se ajustó a la realidad del código)

| Dónde | Antes | Ahora | Por qué |
|---|---|---|---|
| Cabecera | Bloqueada por F-059 y F-038 `done` | F-059 `done`; F-038 mergeada y publicada pero `blocked` (T7) | `harness/features.json`; el orden es C-1 |
| R50 | «Un componente propio» | Lógica en `js/volcado.js`, montada dentro del único `x-data` | `_x_data` de `test_f035_paginas.py` (R70) exige uno solo |
| R51 | Nombres «de la bandeja ya cargada» | Nombres del `catalogo` de `GET /api/revision` | La lista va paginada (100) y no tiene las 285; el catálogo es de la obra |
| R51 | — | Estados por su valor real (`idempotente`, no «ya creado») y ensayo sin `ensayo_id` | `EstadoEvento` y `ensayar` de F-059 |
| R52 | Un volcado por ensayo | Solo por ensayo con algún `previsto` | `_lista` del handler rechaza `incidencias` vacía (400) |
| R53 | Parar ante un no-200 | También sin respuesta del servicio, con algún `sin_respuesta` en un 200 y con el ensayo del trozo caducado | El front aborta a los 40 s sin saber si se escribió; `interpretar_respuesta` puede dar `sin_respuesta` en un 200; 57 trozos |
| R53 | — | `sinReintentos` en ensayo y volcado | `js/api.js` reintenta dos veces un 502 o un corte por defecto |
| R53 | — | Avisos de posible duplicado; re-lectura tras un `idempotente`; «Volver a ensayar» como reanudación | La respuesta de `volcar` trae `avisos`; un `idempotente` de ensayo ya deja `volcada` |
| R54 | Etiquetas, línea y filtros de la lista en esta ficha | Ya los cumple F-038 R21; aquí solo los textos propios del panel | Q-6 de F-038 (2026-10-20) |
| R55 | Un `beforeunload` | La misma guarda de F-038, ampliada | `test_f038_r13_un_solo_beforeunload_que_solo_lee` |
| R57 | Fuera `MaquetaDatos.volcado` | Fuera lo del panel; los catálogos se mudan | `portal_app.js` los usa fuera del panel |
| R58 | README | README, `ARCHITECTURE.md` y `azure-apps/postventa_incidencias.md` | Regla de mantenimiento de `azure-apps/` |

## 5 · Respuestas del humano del 2026-10-28 (qué se aplicó)

| Pregunta | Respuesta | Dónde queda |
|---|---|---|
| C-1 · Orden con F-038 | Como se recomendó: Bloques 1 y 2 ya; el Bloque 3 espera a F-038 `done` | Cabecera, R57; `tasks.md` Bloque 3 |
| C-2 · El volcado de la VILLA 15 | **No es tarea de la ficha**: lo hará el humano cuando el panel esté operativo | §0, §3; el T5 bis esbozado se quita de `tasks.md` |
| C-3 · La obra, no la unidad | Como se recomendó: sin filtro; recuento por unidad en el ensayo y en la confirmación | R51, R52, R61 |
| C-4 · Lo ya dado de alta a mano | **Sincronizar antes de registrar**: botón «Registrar» que lee Sigrid (F-065), enseña qué va, qué ya existe y qué choca, y solo entonces ensaya y vuelca de 5 en 5; lo que existe se excluye, lo que choca pide un segundo clic; la guarda la aplica también el ensayo en el backend (F-065). **F-040 pasa a depender de F-065** | §0, glosario, R50, R60–R62, R51, R53.6, R56 |
| C-5 · Aprobar 285 una a una | Como se recomendó: fuera, es F-043 | §3 |
| C-6 · Verificación en la 0626 | Como se recomendó: T5 en la 0626 tal como se aprobó | `tasks.md` T5 |

Lo que de C-4 dependía del contrato de F-065 (la ruta de la sincronización,
la forma de su respuesta, qué hallazgo es «ya existe» y cuál «choca», de
dónde sale la unidad, cómo viaja al ensayo la inclusión de lo que choca y qué
responde el ensayo si la sincronización ya no vale) quedó pendiente de su
spec; se concilió el 2026-10-31 (§6).

## 6 · Conciliación con F-065 (2026-10-31, T0)

Contra el código de la base fija `f97ec6e` (`services/postventa-api`),
`specs/F-065-revision-sigrid-backend/` (`requirements.md` R41–R49, `design.md`
§15) y `docs/INTEGRACION.md` («Con F-065», l. 235–353).

| Dónde | Ahora | De dónde (fichero:línea) |
|---|---|---|
| Glosario | Sincronización = `GET /api/revision/sigrid?obra=`; los cuatro veredictos en tres grupos (`se_enlaza` dentro de «va», P-1, respuesta del humano 2026-10-31) | `function_app.py` 2074; `domain/models/sigrid_bandeja.py` 127–137, 697–713 |
| R60 | Ruta, una sola petición sin reintento, y sus errores reales (el 503 sin `codigo`) | `function_app.py` 2096–2119, 1335–1361, 1642–1663 |
| R61 | Grupos de `volcado.veredictos`; recuento de `volcado.por_unidad` (unidad vigente); el porqué de cada `choca`, de `reclamaciones` y `hallazgos`; sin `ficha` | `interface_adapters/api/sigrid_bandeja.py` 255–283, 324–352 |
| R62 | `conflictos_confirmados` por incidencia con todos sus códigos; el texto del `choca` por `NPR`; la guarda relee en cada ensayo, sin caducidad de la sincronización | `interface_adapters/api/volcado.py` 238–250, 461–504; `application/pipelines/guarda_sigrid.py` 131–153; F-065 `design.md` §15.4 |
| R51 | Se ensaya lo que nombra la sincronización | — (decisión de diseño, `design.md` §3.1) |
| R54 | Dos motivos de exclusión y tres errores del ensayo más; el 503 sin código | `domain/models/volcado.py` 188–204; `function_app.py` 1877–1916 |
| R55 | La respuesta de la sincronización tampoco se guarda en el navegador | F-065 R35; `function_app.py` 2063–2071 |

Preguntas P-1 a P-3 (`progress/spec_F-040.md`): **respuesta del humano 2026-10-31**, las tres como se recomendaron: P-1 `se_enlaza` dentro de «va», marcada y sumada a su recuento; P-2 casilla por incidencia, sin «todas las de la unidad»; P-3 T5 bis aparte en la 0677, solo ensayos, y F-040 se cierra sin esperarla (`tasks.md`).
