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
> Bloque 3 sí (C-1); aprobar en bloque, fuera (C-5); T5 en la 0626 (C-6). Lo
> que el panel espera del contrato de F-065 va marcado **«a fijar por
> F-065»**: lo fija su spec, no esta.
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
> **Bloqueada por F-065** (decisión del humano del 2026-10-28, C-4): el
> backend que lee las reclamaciones de la obra en Sigrid y las cruza con la
> bandeja (`specs/F-065-revision-sigrid-backend/`, en conciliación en el
> worktree `postventa-f065`) tiene que estar `done`, mergeado en `dev` y
> desplegado antes del Bloque 1 de esta ficha; la rama de F-040 trae ese
> `dev` antes de empezar.
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
- **Sincronización** *(2026-10-28)*: la lectura de las reclamaciones de la
  obra en Sigrid cruzada con la bandeja (F-065), el primer paso de
  «Registrar».
- **Va / ya existe / choca** *(2026-10-28)*: cómo queda cada aprobada tras la
  sincronización. **Va**: no hay nada en Sigrid que la reclame; se ensaya.
  **Ya existe**: Sigrid ya la tiene; se excluye. **Choca**: hay en Sigrid algo
  que se le parece; solo se ensaya con un segundo clic. Qué hallazgo de F-065
  es cada cosa: **a fijar por F-065**.
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
  y sin saltarse ninguno: (1) pedir a F-065 las reclamaciones de la obra en
  Sigrid cruzadas con la bandeja; (2) enseñar el resultado (R61) y esperar;
  (3) solo con un clic más, ensayar y volcar como dicen R51–R53. SI la
  sincronización no responde bien o queda sin respuesta del servicio,
  ENTONCES el panel debe parar ahí: **no** ensaya ni deja ensayar, y lo dice.
  La ruta, la forma de la respuesta y sus errores: **a fijar por F-065**.
- **R61.** Tras la sincronización, el panel debe enseñar cada candidata en
  uno de tres grupos —**va**, **ya existe** (con el código de Sigrid de lo que
  ya existe) y **choca** (con lo que choca en Sigrid y por qué)— y el
  **recuento por unidad** de cada grupo (C-3), con el nombre de la unidad del
  `catalogo` de `GET /api/revision`. Qué hallazgos de F-065 caen en cada
  grupo, y de qué campos sale la unidad: **a fijar por F-065**.
- **R62.** Lo que **ya existe** en Sigrid se excluye: no se ensaya ni se
  vuelca, y no hay botón que lo incluya. Lo que **choca** no se ensaya salvo
  que la persona lo incluya con un **segundo clic** explícito; sin él, se
  queda fuera y sale como tal en el resultado. El backend aplica la misma
  guarda en el ensayo (F-065), así que el panel no es la única defensa; cómo
  viaja al ensayo la decisión de incluir lo que choca, y qué responde el
  ensayo si la sincronización ya no vale: **a fijar por F-065**.

### 1.2 · Ensayo y volcado

- **R51.** CUANDO, tras la sincronización (R60), se pide el ensayo, el panel
  debe partir **las que van** (y las que chocan incluidas con su segundo
  clic) en trozos de `partes_por_llamada`, pedir los ensayos
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
  `huella_no_coincide`, `fuera_del_ensayo`, `revision_desactualizada`), para
  cada causa de `ensayo_no_valido` (`no_existe`, `de_otra_obra`,
  `de_otra_persona`, `caducado`) y para cada `codigo` de error de las tres
  rutas; los códigos de §8.9 los traduce `Revision.textoMotivoVolcado`, sin
  copiar su tabla. Un código desconocido sale tal cual.
- **R55.** Ni el correo ni el `oid` van a `console` ni al almacenamiento del
  navegador. MIENTRAS haya una serie de ensayos o de volcados en marcha, salir
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

Lo que de C-4 depende del contrato de F-065 (la ruta de la sincronización,
la forma de su respuesta, qué hallazgo es «ya existe» y cuál «choca», de
dónde sale la unidad, cómo viaja al ensayo la inclusión de lo que choca y qué
responde el ensayo si la sincronización ya no vale) queda **«a fijar por
F-065»**: lo fija su spec, que se está conciliando en `postventa-f065`. Antes
del Bloque 1 de esta ficha, el spec-author vuelve a conciliar R60–R62 y
`design.md` §1.1 con el contrato de F-065 tal como quede en `dev`.
