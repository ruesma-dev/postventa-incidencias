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
> 2026-10-27»), pendientes del humano.
>
> **Partida por D-1 (decisión del humano del 2026-10-07).** El backend —ensayo,
> volcado, tabla `volcados_sigrid`, estados `volcada` y `en_duda`, ventana
> `VOLCADO_HABILITADO`, verificación de la escritura en producción— es la
> ficha **F-059** (`specs/F-059-volcado-sigrid-backend/`), **`done`**:
> desplegada el 2026-10-17 y verificada en producción el 2026-10-19 (obra 0626,
> un parte, anulado después). **Esta ficha es el front**: el panel de volcado
> en `bandeja.html` y el cierre de los restos de F-040 en el portal.
> *(Conciliado 2026-10-27: F-038 está mergeada en `dev` y `bandeja.html`
> publicada, pero la ficha sigue `blocked` a la espera de su T7 manual; qué
> bloques de F-040 pueden ir antes de que F-038 esté `done` es la pregunta
> C-1.)*
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

**El volumen real (conciliado 2026-10-27).** El primer uso previsto es la
VILLA 15 de la 0677: unas **285** incidencias importadas por Excel, que con
`partes_por_llamada` = 5 son **57 trozos**, 57 ensayos y 57 volcados de uno en
uno. Lo medido en la verificación de F-059 (2026-10-19, un parte): ensayo de
1,2 s a 5,8 s, volcado 1,8 s, y un primer ensayo tras abrir la ventana de
**35 s** (arranque en frío de `sigrid-api`). Con esas cifras la obra entera
cabe en los 30 minutos de vida de un ensayo, pero no con holgura si la
pasarela va lenta; los requisitos de abajo (R51 a R53) dicen qué pasa cuando
no cabe.

## 0.1 · Glosario

Los de F-059 (candidata, referencia, ensayo, volcado, llamada, en duda), más:

- **Trozo**: grupo de como mucho `partes_por_llamada` incidencias (el valor
  que devuelve `GET /api/volcado`, hoy 5); un ensayo y un volcado por trozo.
- **Ensayo de la obra**: el conjunto de los ensayos de todos los trozos,
  enseñados juntos.
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
  trozos irán, y el aviso de que el ensayo no crea nada.
- **R51.** CUANDO se pulsa **«Ver qué se crearía en Sigrid»**, el panel debe
  partir las candidatas en trozos de `partes_por_llamada`, pedir los ensayos
  **de uno en uno** con su progreso («trozo k de M») y enseñar, juntos, cada
  parte con su unidad, oficio y proveedor (el nombre del `catalogo` de la
  respuesta de `GET /api/revision` que la página ya tiene; sin nombre, el
  código del `envio`), ubicación, descripción, tipo (`0002` PRIMER LISTADO
  POSTVENTA) y estado (`previsto` → `Se crearía`; `idempotente` → `Ya estaba
  creado`; `rechazado` → `No se crea` con el texto de su motivo;
  `no_procesado` → `No se llegó a intentar` con el texto de su motivo), y las
  excluidas con el texto de su motivo. Un ensayo que responde 200 sin
  `ensayo_id` (nada que mandar en ese trozo) es un trozo sin previstos, no un
  fallo. SI un ensayo no responde 200 —o queda sin respuesta del servicio—,
  ENTONCES el panel debe parar la serie (no pide los trozos siguientes),
  decir por qué y no habilitar el volcado.
- **R52.** **«Volcar N partes a Sigrid»** (N = la suma de los `previsto` de
  todos los ensayos) solo se habilita con al menos un `previsto`, con todos
  los ensayos en 200, con la caducidad más temprana sin alcanzar (cuenta atrás
  visible) y sin ninguna petición en vuelo, y tras una **confirmación
  explícita** (**D-12**: segundo clic y teclear el número de partes). Manda un
  volcado por cada ensayo **que tenga algún `previsto`**, con su `ensayo_id` y
  solo sus `previsto`, cada uno con la `revision_id` de su parte del ensayo; un
  ensayo sin previstos no se manda (el backend rechaza una lista vacía con
  400). `confirmado: true` aparece en **una sola** función de `js/volcado.js`.
- **R53.** Los volcados se piden **de uno en uno**, en el orden de los
  ensayos, y:
  1. ANTES de mandar cada trozo, SI su ensayo ya ha caducado (su
     `caduca_at_utc`), ENTONCES el panel debe parar sin mandarlo y decir que
     hay que volver a ensayar lo que queda *(conciliado 2026-10-27: con 57
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
  6. **«Volver a ensayar»** es el único reintento: lo pulsa una persona y
     ensaya las candidatas que devuelve el panel en ese momento (que ya no
     incluyen las volcadas y sí las en duda, F-059 R27). Es como se reanuda un
     volcado parado.
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
- **R56.** Nada sale sin un clic: cargar el panel solo lee; ensayar y volcar
  solo desde `@click`; con una petición en vuelo, ningún botón de ensayo ni de
  volcado.
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
  guardias de F-035 siguen en verde; F-039 y F-043 conservan sus restos. El
  orden respecto al cierre de F-038 es la pregunta C-1.
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
| Aprobar en bloque | **F-043** (ver C-5) |
| Filtrar el volcado por unidad | Nadie hoy: el panel vuelca la obra (ver C-3) |
| Detectar lo ya dado de alta a mano en Sigrid | **F-064 / F-065** (ver C-4) |
| El primer volcado masivo de la 0677 y el ajuste de `N` | Más adelante (Q-8; ver C-2) |
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
