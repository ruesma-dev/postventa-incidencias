<!-- progress/spec_F-040.md -->
# Spec de F-040 (y de F-059) · resumen para el líder

> spec-author, 2026-10-07. Worktree `postventa-f040`, rama
> `feature/F-040-volcado-sigrid` (desde `dev` `f86d639`). **Aprobada por el
> humano el 2026-10-07**: D-1 a D-14 como se recomendaban y Q-1 a Q-8
> respondidas. Por D-1 la spec está **partida en dos carpetas**:
>
> - `specs/F-059-volcado-sigrid-backend/` — el backend (R1–R43), va **antes**.
> - `specs/F-040-volcado-sigrid/` — el front (R50–R59), bloqueada por F-059 y
>   por F-038.
>
> No se ha ejecutado `init.sh` ni pytest (autorizado). Ni código, ni
> `features.json`, ni `BACKLOG.md`, ni `current.md` tocados.

## Lo que el líder tiene que hacer

1. **Dar de alta F-059** en `harness/features.json` (propuesta abajo) y
   llevar `specs/F-059-volcado-sigrid-backend/` a su rama cuando empiece.
2. **Actualizar F-040**: descripción (es el front, bloqueada por F-059 y
   F-038), `blocked_by`, y que la spec está aprobada.
3. Al desplegar F-059 (su T24), la fila de consumidores de
   `azure-apps/sigrid_api.md` §10 (Q-6).

### Propuesta de ficha F-059

- **id**: `F-059`
- **title**: «Volcado a Sigrid en el backend: ensayo, escritura en lote y
  estado volcada»
- **branch**: `feature/F-059-volcado-sigrid-backend`
- **rigor**: `critico` · **sdd**: `true` · **status**: `spec_ready` (cuando
  F-056 esté `done`) · **priority**: justo antes de F-040
- **blocked_by**: «F-056 (las candidatas al volcado y los estados de
  revisión), que tiene que estar done y mergeada en dev».
- **description**: «Sacada de F-040 el 2026-10-07 por el límite de servicio
  (D-1, decisión del humano). El backend del volcado de la bandeja a Sigrid
  en services/postventa-api: tres endpoints (GET /api/volcado,
  POST /api/volcado/ensayo, POST /api/volcado/volcar) sobre
  POST /api/sigrid/partes-reclamacion de sigrid-api (azure-apps/sigrid_api.md
  §8.9); ensayo guardado obligatorio (misma persona, 30 min); escritura
  anticipada del evento enviado antes de cada commit; referencia
  PVI-<incidencia_id> para que reintentar no duplique; tabla append-only
  postventa.volcados_sigrid (16_volcados_sigrid.sql); estados derivados
  volcada y en_duda que amplían los de F-056 y bloquean la revisión; tipo
  0002 siempre, causante false, sin urgencia ni clase; el parte queda en SAT
  y Posventa lo pasa a PTE a mano; ventana propia VOLCADO_HABILITADO
  publicada cerrada (infra/27_ventana_volcado.ps1) y lectura de verificación
  (infra/28_volcado_lectura_sigrid.ps1); verificación en producción en la
  obra 0626 con una escritura autorizada y anulación posterior. Spec:
  specs/F-059-volcado-sigrid-backend/. El front es F-040.»
- **acceptance**:
  1. «Una incidencia aprobada se crea en Sigrid con sus campos (tipo 0002,
     oficio, ubicación, interviniente sin causante) y su código vuelve a la
     bandeja como volcada»
  2. «No se escribe en Sigrid sin un ensayo guardado de la misma persona de
     menos de 30 minutos, con confirmado true y con la ventana
     VOLCADO_HABILITADO abierta; el despliegue la deja cerrada»
  3. «Reintentar no duplica: la misma referencia PVI- vuelve idempotente;
     un tiempo agotado deja la incidencia en_duda y el reintento la recupera»
  4. «Un lote de N filas crea N partes; si uno falla se sabe cuál y por qué»
  5. «Una incidencia volcada o en duda no se puede editar, descartar ni
     aprobar»
  6. «Ni propietario, ni persona, ni correo, ni oid, ni login, ni textos en
     ningún log»
  7. «Verificado en producción en la obra 0626 con una escritura autorizada,
     anulada después en la UI de Sigrid»
  8. «docs/ y azure-apps/postventa_incidencias.md al día»
  9. «bash harness/init.sh en verde»

### Ajuste propuesto de F-040

- **description** (añadir): «PARTIDA EL 2026-10-07 (D-1, decisión del
  humano): esta ficha es el panel de volcado en bandeja.html (ensayar,
  confirmar con el número de partes, volcar de trozo en trozo, parar al
  primer fallo, aviso de pasar a PTE a mano) y el cierre de sus placeholders
  del portal; el backend es F-059. Spec aprobada:
  specs/F-040-volcado-sigrid/.»
- **blocked_by**: «F-059 (el backend del volcado), done, desplegada y
  verificada; y F-038 (bandeja.html), done.»
- Los acceptance actuales siguen valiendo, cumplidos entre F-059 (backend) y
  F-040 (la página).

## Qué decide la spec (con las respuestas del humano)

- **Flujo**: candidatas → ensayo guardado → confirmación → volcado (solo lo
  `previsto`, misma persona, misma revisión) → resultado de vuelta a la
  bandeja (`volcada` con su `RS…`, `en_duda` o `aprobada` con su motivo).
- **Q-1** tipo `0002` siempre; **Q-2** `causante: false`; **Q-3** el parte
  queda en SAT y Posventa lo pasa a PTE a mano (en la documentación, en el
  panel —R59— y en la verificación, que **no** lo pasa a PTE); **Q-4** obra
  0626; **Q-5** recrear un parte anulado, fuera; **Q-6** sí, la fila de
  `sigrid_api.md` la escribe el líder al desplegar; **Q-7** cualquiera del
  grupo con login de Sigrid; **Q-8** el primer volcado masivo de la 0677 y el
  ajuste de `N`, **pendiente fuera de alcance**.
- **D-3** la ventana `VOLCADO_HABILITADO` se publica **cerrada** en cada
  despliegue y se abre con `27_ventana_volcado.ps1` para cada volcado.

## Riesgos

1. **El coste por parte no está medido**: `N`=5 conservador, App Setting; el
   ajuste es Q-8, más adelante.
2. **Tras nuestro tiempo agotado, `sigrid-api` sigue creando** (150 s): queda
   `en_duda` y el reintento lo recupera.
3. **Depende del código de F-056 tal como quede**: si los nombres difieren de
   su design, el implementer de F-059 para (su T0).
4. **Los partes quedan en SAT** hasta que Posventa los pase a PTE: si no lo
   hace, el industrial no se entera.
5. **Escritura real en una obra en uso** (0626) en las dos verificaciones: una
   cada vez, autorizada, sin PTE, anulada al terminar. El parte de prueba de
   F-006 de `sigrid-api` en la 0626 sigue sin anular.

## Conciliación 2026-10-27

> spec-author, 2026-10-27. Worktree `postventa-f040`, rama
> `feature/F-040-volcado-sigrid` (de nuevo desde `dev` `f7f63da`, commit
> `59ce4c9`; la de antes queda en `archivo/F-040-spec-2026-10-07`). Contraste
> de `specs/F-040-volcado-sigrid/` con el código de `dev`: F-059 tal como se
> cerró y desplegó, `bandeja.html` y `js/revision.js` de F-038 publicados, y
> F-060. Sin red, sin base, sin Sigrid, sin SharePoint. Ni código, ni
> `features.json`, ni `BACKLOG.md`, ni `current.md` tocados.

### Qué cambió (ajustes a la realidad del código, ya aplicados)

Cada fichero lleva su nota y su tabla: `requirements.md` §4, `design.md` §9,
y las marcas «(conciliado 2026-10-27)» de `tasks.md`. Lo de más peso:

1. **El contrato es el implementado** (`design.md` §1): cuerpos con
   exactamente sus claves, `resumen` con sus claves por modo (`previstos`,
   `idempotentes`… / `creados`, …, `sin_respuesta`), un ensayo o un volcado sin
   nada que mandar responde 200 con los ids **nulos**, la respuesta de
   `volcar` trae `avisos` (posible duplicado, F-059 R26) y la lista completa
   de códigos de error con su HTTP (`CODIGOS_DEL_VOLCADO` /
   `HTTP_DEL_VOLCADO`), incluidos los que la spec no nombraba
   (`ensayo_sin_respuesta` también en `volcar`, antes de escribir; los dos del
   login; `bandeja_demasiado_grande`; los 503 de configuración y base).
2. **`js/api.js` reintenta solo por defecto**: dos veces un 502 o un corte.
   Las dos peticiones que escriben o ensayan van `sinReintentos: true` y las
   tres con `mensajeDelServicio` (sin él, un 503 sale con el texto de la
   puerta de archivar). Sin esto, un 502 `volcado_sin_respuesta` se habría
   reintentado solo: justo lo que prohíbe R53.
3. **Parar es más que «un no-200»** (R53): también si el front se queda sin
   respuesta (aborta a los 40 s y el backend puede seguir escribiendo), si un
   200 trae algún parte `sin_respuesta` (`interpretar_respuesta` lo da sin
   levantar el 502) y si el ensayo del trozo ya ha caducado antes de mandarlo.
   Es más estricto que lo aprobado, no lo contradice; si el humano prefiere
   seguir en el caso del 200 con `sin_respuesta`, es una línea.
4. **Un solo `x-data`** (R50, `design.md` §3.3): la guardia R70 de F-035
   (`_x_data`) exige un único elemento con `x-data` por página, así que el
   «componente propio» es lógica en `js/volcado.js` montada bajo la clave
   `volcado` de `appRevision`. `js/revision.js` se toca lo mínimo (la
   composición y un aviso en `cargar()`).
5. **R54 ya está hecho por F-038 R21** (su Q-6, 2026-10-20): etiquetas, línea
   y filtros de `volcada` y `en_duda`, y los textos de §8.9. Aquí quedan los
   textos propios del panel (7 motivos de exclusión, 4 causas de
   `ensayo_no_valido`, los códigos de error), reutilizando
   `Revision.textoMotivoVolcado`.
6. **Nombres del ensayo desde el `catalogo`** de `GET /api/revision`, no de
   las filas cargadas: la lista va paginada (100) y con 285 no estarían todas.
7. **La guarda de salida es la de F-038, ampliada** (una sola,
   `test_f038_r13_…`).
8. **R57 no puede borrar `MaquetaDatos.volcado` entero**: sus `catalogos`
   (`tipos`, `formas`, `oficios`) los usan `tipo()`, `forma()` y `oficio()` de
   `js/portal_app.js` en las secciones de incidencias; se mudan. Lista exacta
   de restos en `design.md` §4, con los tests que solo les servían.
9. **R58 crece**: además del README, `docs/ARCHITECTURE.md` y
   `azure-apps/postventa_incidencias.md` (cita F-040 en futuro en tres
   sitios); nueva T6 bis.
10. **Sin merge previo en el Bloque 1**: la rama ya sale de un `dev` con
    F-059.
11. **Tests de otros que el panel obliga a tocar**, nombrados: los de
    `tests/test_f038_front.py` (cinco scripts, guarda, rutas),
    `tests_js/revision.test.js` (el recorrido de `bandeja.html`),
    `tests_js/api.test.js` (de 20 a 23 endpoints).

**El volumen real** (285 incidencias, 57 trozos de 5) cabe en el diseño: con
lo medido en T25 de F-059 (ensayo 1,2–5,8 s, volcado 1,8 s, un arranque en
frío de 35 s), del orden de 3–10 minutos de ensayos y otro tanto de volcados.
Lo que cambia en la experiencia está ya en R51–R53: progreso «trozo k de M»,
no mandar un trozo con el ensayo caducado (el trozo 1 es el primero que
caduca), parar en el primer fallo y **reanudar** con «Volver a ensayar», que
ensaya lo que el panel devuelve en ese momento —sin las volcadas, con las en
duda—. Un `idempotente` en un ensayo ya deja la incidencia `volcada`, así que
tras los ensayos se relee el panel.

### Preguntas para el humano (no aplicadas)

- **C-1 · El orden con F-038.** `blocked_by` de F-040 pide F-038 `done`, y
  F-038 está `blocked` a la espera de su T7 (verificación manual de
  `bandeja.html` en producción). `bandeja.html` está en `dev` y publicada, así
  que el Bloque 1 y el Bloque 2 no la necesitan cerrada. El Bloque 3 sí: si
  F-040 cierra antes, la sección `bandeja` pasa a `parcial` por F-040 (R62 de
  F-035) y su commit de cierre arrastra la marca de la barra en todas las
  páginas reales, que es el trabajo del cierre de F-038. **Recomendación:**
  Bloques 1 y 2 ya; el Bloque 3 espera a que F-038 esté `done`.
- **C-2 · El volcado de la VILLA 15 y Q-8.** Q-8 dejó «el primer volcado
  masivo de la 0677 y el ajuste de N» fuera de la ficha, y ahora es justo lo
  que Posventa quiere hacer con el panel. **Recomendación:** añadir un T5 bis
  MANUAL (está esbozado en `tasks.md`, sin aprobar): tras T5, el volcado real
  de la VILLA 15 con autorización expresa, primero un trozo y su foto con
  `28_`, luego el resto; `N` se queda en 5 y las duraciones se anotan para
  ajustarlo más adelante (esa parte de Q-8 sigue fuera).
- **C-3 · El panel vuelca la obra, no la unidad.** `GET /api/volcado` da las
  candidatas de **toda** la 0677; si hay aprobadas de otras unidades, irían
  también. Filtrar por unidad pediría cambiar el backend (F-059).
  **Recomendación:** no filtrar en F-040; que el ensayo enseñe el recuento por
  unidad (de `envio.unidad_postventa`, con su nombre) y la confirmación lo
  diga («285 de VILLA 15 y k de otras»). Es un añadido pequeño al panel, por
  eso se pregunta.
- **C-4 · Lo ya dado de alta a mano en Sigrid.** El volcado solo reconoce sus
  propios partes (`PVI-`): si Posventa ya creó a mano alguna incidencia de la
  VILLA 15, se duplicaría. F-064/F-065 (cruzar la bandeja con Sigrid) se
  aprobaron el 2026-10-20 para ir **antes** de F-040 por esto mismo.
  **Recomendación:** F-040 no cambia; antes del volcado real, el humano
  confirma con Posventa que la VILLA 15 no está dada de alta a mano (o se
  espera a F-065).
- **C-5 · Aprobar 285 una a una.** Solo lo aprobado es candidato, y aprobar
  en bloque es F-043 (`pending`). Fuera del alcance de F-040.
  **Recomendación:** no ampliar F-040; si aprobar de una en una no es
  asumible, priorizar F-043 (o una parte de ella) antes del volcado real.
- **C-6 · La verificación en la 0626 (Q-4).** T5 escribe un parte de prueba
  en la 0626 y lo anula, como F-059. Con el volcado real tan cerca, cabría
  hacer los pasos sin escritura (ventana cerrada, 503) en la propia 0677 y que
  la primera escritura sea el primer trozo real de la VILLA 15, sin parte de
  prueba ni anulación. **Recomendación:** mantener la 0626 tal como se aprobó:
  es la primera vez que este código escribe y lo barato es equivocarse con un
  parte que se anula; el primer trozo real va después (C-2).

### Respuestas del humano (2026-10-28), ya aplicadas

> spec-author, 2026-10-28, mismo worktree y rama. F-040 queda `blocked`
> hasta que se cierre F-065; el backlog lo lleva el líder en la rama de F-065
> (aquí no se han tocado `features.json`, `BACKLOG.md` ni `current.md`).

| Pregunta | Respuesta | Qué se cambió |
|---|---|---|
| C-1 | Como se recomendó | Bloques 1 y 2 sin esperar a F-038; Bloque 3 (T6) solo con F-038 `done` (requirements cabecera y R57, design §1 y §4, tasks Bloque 3) |
| C-2 | El volcado de la VILLA 15 **no es tarea** de la ficha: lo hará el humano con el panel operativo | Quitado el T5 bis esbozado; requirements §0 y §3; design §6 (Q-8 confirmada) |
| C-3 | Como se recomendó: sin filtro, recuento por unidad en el ensayo y en la confirmación | R51, R52, R61; design §2 y §3.1 (`recuentoPorUnidad`); tests |
| C-4 | **Sincronizar antes de registrar.** Botón «Registrar» (filosofía de `dedicacion`): (1) trae las reclamaciones de la obra desde Sigrid y las cruza con las aprobadas (backend de F-065, que va antes); (2) enseña qué va, qué ya existe y qué choca, con el recuento por unidad; (3) solo entonces ensaya y vuelca de 5 en 5. Lo que ya existe se excluye; lo que choca pide un segundo clic; la guarda la aplica también el ensayo en el backend (F-065) | Requisitos nuevos **R60–R62**; glosario (sincronización, va / ya existe / choca); R50 («Registrar» como único botón de entrada), R51, R53.6 («Volver a registrar» desde la sincronización), R56; design §1.1 (lo que el panel espera de F-065), §2, §3.1–§3.3, §7, §8 (riesgos 9–11); tasks: nuevo **Bloque 0 / T0** (merge del `dev` con F-065 como base fija y reconciliación de R60–R62 con su contrato), T1–T3 y T5.2 |
| C-5 | Como se recomendó: aprobar en bloque, fuera (F-043) | requirements §3 |
| C-6 | Como se recomendó: T5 en la 0626 | tasks T5; design §6 (Q-4 confirmada) |

**Lo que queda «a fijar por F-065»** (no inventado aquí; lo fija la spec que
se está conciliando en `postventa-f065`): la ruta y la forma de la respuesta
de la sincronización y sus errores; qué hallazgos son «ya existe» y cuáles
«choca»; de dónde sale la unidad de cada candidata para el recuento previo al
ensayo (hoy `GET /api/volcado` no la trae); cómo viaja al ensayo la inclusión
de lo que choca y si el segundo clic es por incidencia o en bloque; cómo dice
el ensayo lo que excluye por la guarda y qué responde si la sincronización ya
no vale; y si la lectura de una obra como la 0677 cabe en los 40 s del front.
Está todo en `design.md` §1.1. T0 lo concilia con el contrato implementado
antes del Bloque 1.

**Para el spec-author de F-065**, por si no lo tiene ya: el panel necesita,
por cada candidata de `GET /api/volcado`, su grupo (va / ya existe / choca),
el código de Sigrid de lo que ya existe, lo que choca y por qué, y su unidad;
y que el ensayo excluya, con un motivo que se pueda traducir, lo que ya existe
y lo que choca sin incluir.

Sin preguntas abiertas nuevas.

## Conciliación con F-065 (2026-10-31, T0)

> spec-author, worktree `postventa-f040`, rama `feature/F-040-volcado-sigrid`,
> base fija **`f97ec6e`** (merge de `dev` `7cc0bbb`: F-065 `done`, desplegada
> desde `ed590bd`), anotada en `progress/impl_F-040.md`. Sin tocar código ni
> tests; `init.sh` no se ha ejecutado (lo corre el líder). Fuentes, en este
> orden: código de `services/postventa-api`, `specs/F-065-revision-sigrid-backend/`
> (R41–R49, `design.md` §15) y `docs/INTEGRACION.md` (l. 235–353).

### Qué cambió

`grep -rn "fijar por F-06[5]" specs/F-040-volcado-sigrid/` ya no da nada.

| Fichero · sitio | Cambio | Fuente (fichero:línea, en `services/postventa-api/` salvo que se diga) |
|---|---|---|
| `requirements.md` cabecera | Nota de la conciliación; «Bloqueada por F-065» pasa a «Dependía de F-065» con la base fija | `harness/features.json` (F-040), `git log` `f97ec6e` |
| `requirements.md` glosario | Sincronización = `GET /api/revision/sigrid?obra=`; los cuatro veredictos en tres grupos: va = `va` + `se_enlaza` (P-1), ya existe = `ya_existe`, choca = `choca` (también el `PVI-` anulado o de estado desconocido) | `function_app.py:2074`; `domain/models/sigrid_bandeja.py:127-137`, `:697-713` |
| `requirements.md` R60 | Ruta, una petición sin reintento, y los errores reales: 400 `peticion_invalida`; 409 `bandeja_demasiado_grande` (`total`), `reclamaciones_sin_verificar` (`filas`), `obra_ambigua`; **503 sin `codigo`** | `function_app.py:2096-2118`, `:1335-1341`, `:1344-1361`, `:1642-1663` |
| `requirements.md` R61 | Grupos de `volcado.veredictos` (`{incidencia_id, unidad_codigo, estado, veredicto, sigrid_cods}`); recuento de `volcado.por_unidad` (unidad vigente, cuatro claves siempre); el porqué de un choque desde `reclamaciones` (emparejada → anulada) y `hallazgos` (`criterios`, `parecido`); sin `ficha` | `interface_adapters/api/sigrid_bandeja.py:255-283`, `:324-352` |
| `requirements.md` R62 | Segundo clic **por incidencia** (P-2); viaja en `conflictos_confirmados: [{incidencia_id, sigrid_cods}]` con **todos** los códigos del veredicto y solo las del trozo; texto propio para el `choca` por parte anulado (enlaza con él); la guarda relee Sigrid en cada ensayo, así que la sincronización no caduca: lo que cambió sale como `duplicada_en_sigrid` / `conflicto_sin_confirmar` y se ofrece «Volver a registrar» | `interface_adapters/api/volcado.py:238-250`, `:461-504`; `application/pipelines/guarda_sigrid.py:131-153`; F-065 `design.md` §15.4; F-065 R45 (enmienda a S-3) |
| `requirements.md` R51 | Se ensaya lo que nombra la sincronización; lo aprobado después se cuenta aparte y pide volver a registrar | Decisión de diseño (no hay `sincronizacion_id`: F-065 §15.4) |
| `requirements.md` R54 | Textos para `duplicada_en_sigrid`, `conflicto_sin_confirmar`, `sigrid_no_disponible`, `reclamaciones_sin_verificar`, `obra_ambigua` y el 503 sin código | `domain/models/volcado.py:188-204`; `function_app.py:1877-1916` |
| `requirements.md` R55 | La respuesta de la sincronización (datos personales, `no-store`) no va al almacenamiento ni a `console` | F-065 R35; `function_app.py:2063-2071` |
| `requirements.md` §5, §6 | El párrafo «a fijar» pasa a pasado; §6 nuevo con la tabla de la conciliación | — |
| `design.md` cabecera, §1 | Nota; F-065 `done` y su base fija; el ensayo gana clave, bloque, motivos y errores; `GET /api/volcado` y `volcar` sin cambios | F-065 R49; `interface_adapters/api/volcado.py:231-301` |
| `design.md` §1.1 | La tabla de necesidades se sustituye por el contrato implementado: la ruta y su 200, los veredictos y su precedencia, los errores, el tiempo medido (0677: p50 0,67 s, máx. 4,70 s, 1,3 MB); la guarda (cuerpo, exclusiones, `sigrid`, tres errores, la línea de log); la diferencia ruta/guarda con un `PVI-` en otra unidad | `sigrid_bandeja.py:236-352`; `function_app.py:1877-1961`, `:2063-2119`; `guarda_sigrid.py:96-223`; `docs/INTEGRACION.md:319-325`; `progress/impl_F-065.md:3084` (T-A15) |
| `design.md` §2 | Paso 2 con `se_enlaza` en va, el porqué, las no sincronizadas y la casilla por incidencia | §1.1 |
| `design.md` §3.1 | Firmas cerradas: `agruparSincronizacion(candidatas, respuesta, catalogo)`, `paraEnsayar(grupos, incluidas)`, `cuerpoDeEnsayo(obra, ids, identidad, confirmados)`; nuevas `confirmadosDelTrozo`, `excluidasDeLaGuarda`, `textoVeredicto`, `textoPorque`; el panel guarda solo lo que enseña, sin `ficha` | §1.1 |
| `design.md` §3.2 | Tablas de paradas de la sincronización y del ensayo por la guarda, código a código | `function_app.py:2096-2118`, `:1892-1915` |
| `design.md` §3.3 | `revisionSigrid(obra)` con `mensajeDelServicio` y `sinReintentos: true` (lectura pesada y con datos personales; la repite la persona) | `services/postventa-front/js/api.js:280-320` (`peticion`) |
| `design.md` §5 | `LOS_ENDPOINTS` de 20 a **24** (F-065 no tocó el front; F-064 no está en `dev`) | `services/postventa-front/tests_js/api.test.js:206-231` |
| `design.md` §7, §8, §10, §11 | Tests de R60–R62 contra la forma real; riesgos 9 y 10 con lo medido; riesgo 12 nuevo (ruta y guarda difieren); §11 nuevo con el resumen | — |
| `tasks.md` | Nota; T0 con la base y la verificación por `grep` que no se encuentra a sí misma; T1 con las funciones y los 24 endpoints; T5.2 con lo que sale en la 0626; **T5 bis nueva = T-A18 de F-065** (pendiente de P-3); T6 espera a T5 bis si P-3 lo pide | F-065 `tasks.md:373-385` |
| `progress/impl_F-040.md` | Nuevo, con la base fija `f97ec6e` | — |
| `progress/current.md` | Una línea en el bloque de F-040 | — |

### Observación para el líder (no es de F-040)

- La docstring de la ruta, `function_app.py:2081-2082`, lista el 200 **sin**
  `volcado`, que sí sale (`interface_adapters/api/sigrid_bandeja.py:251`). Es
  código de F-065 (`done`); no se toca aquí.
- El encargo nombraba «503 `sigrid_no_disponible`» para las dos rutas: ese
  código es **solo del ensayo** (`function_app.py:1893`); la ruta de la
  sincronización responde 503 **sin** `codigo` (`:2111-2118` →
  `_sin_sigrid_o_sin_base`, `:1344-1361`). La spec lo refleja así.

### Preguntas para el humano (3)

La spec está escrita con la recomendación de cada una, marcada «(P-n)».
Ninguna se ha tomado como decidida.

- **P-1 · Dónde va `se_enlaza`.** C-4 aprobó **tres** grupos (va / ya existe
  / choca) y «lo que ya existe se excluye». F-065 da **cuatro** veredictos: el
  cuarto, `se_enlaza`, es una candidata cuya **propia** reclamación (con su
  `PVI-`) ya está en Sigrid y no anulada; F-065 la **manda** (S-3, aprobada:
  si se excluyera, una `en_duda` no saldría nunca de ahí) y el ensayo la
  devuelve `idempotente` («Ya estaba creado»), sin crear otra. Choca con la
  letra de C-4 porque «Sigrid ya la tiene» y no se excluye.
  **Recomendación**: dentro de **va**, marcada «se enlaza con RS…» y sumada al
  recuento de va. Alternativas: (b) un cuarto grupo visible «ya registrada
  desde aquí: se enlaza», que también se ensaya; (c) excluirla en el panel
  (contradice S-3 y deja las `en_duda` atascadas).
- **P-2 · El segundo clic de lo que choca, por incidencia o en bloque.** El
  diseño del 2026-10-28 (§2) lo dejó abierto «hasta el contrato de F-065», y
  F-065 admite los dos (§15.4: el cuerpo va siempre por incidencia).
  **Recomendación**: una casilla **por incidencia**, cada una con sus
  reclamaciones a la vista; en la 0677 se midieron 7 incidencias con
  conflicto de 466 (T-A13), así que no hay volumen que pida el bloque.
  Alternativa: además, «incluir todas las que chocan de esta unidad».
- **P-3 · Dónde se hace la T-A18 de F-065, y si choca con C-6 y C-2.** La
  T-A18 pide hacerla en el **primer ensayo real de la 0677** con
  «Registrar». C-6 deja T5 (la verificación con escritura) en la **0626**, y
  ahí no hay nada que choque (7 reclamaciones; la única abierta es una `SAT`),
  así que dentro de T5 solo se podría provocar un `choca` importando y
  aprobando otra fila de prueba hecha para parecerse a esa `SAT`. Y C-2 dice
  que el volcado de la VILLA 15 no es tarea de la ficha.
  **Recomendación**: una **T5 bis** aparte, **solo ensayos** (`commit:
  false`) en la 0677, con autorización expresa, sin volcar: no toca C-6 (T5
  sigue en la 0626) ni C-2 (no se vuelca nada). Ya escrita así en
  `tasks.md`. Preguntas concretas: (a) ¿T5 bis en la 0677 o, en su lugar,
  provocar el `choca` en la 0626 dentro de T5?; (b) ¿el cierre (T6, Bloque 3)
  espera a T5 bis o se cierra F-040 con T5 bis pendiente y se anota como
  hecha cuando el humano empiece la 0677?
