<!-- specs/F-040-volcado-sigrid/design.md -->
# F-040 · Volcar a Sigrid las incidencias aprobadas (el panel de volcado) — Diseño técnico

> **Aprobado por el humano el 2026-10-07.** Es el **tramo B** de la spec
> conjunta, partida por D-1: esta ficha es solo `services/postventa-front`.
> El backend, su contrato y todas las decisiones de escritura en el ERP son
> **F-059** (`specs/F-059-volcado-sigrid-backend/design.md`, sobre todo §3,
> §4, §11 y §20).
>
> **Conciliado con `dev` el 2026-10-27** (`dev` `f7f63da`): el contrato de §1
> es el **implementado** (`services/postventa-api/interface_adapters/api/volcado.py`
> y `function_app.py`, «F-059 · el volcado a Sigrid»), no el de la spec de
> F-059; §2 y §3 encajan el panel en el `bandeja.html` y el `js/revision.js`
> publicados de F-038; §5 nombra los tests de F-035, F-036 y F-038 que el panel
> obliga a tocar. Cada cambio lleva «(conciliado 2026-10-27)» y la tabla del
> §9 los resume. Las decisiones que la conciliación pondría en cuestión son
> C-1 a C-6 de `progress/spec_F-040.md`, sin aplicar.

## 0 · Dónde está el riesgo

La puerta de verdad (qué se escribe, cuándo, y que no se duplique) es del
backend, F-059. Lo que esta página puede romper:

| Si falla… | Consecuencia |
|---|---|
| Un volcado sale sin clic, dos veces, o sin haber enseñado el ensayo | Se crean en el ERP partes que nadie miró (el backend exige ensayo de la misma persona, pero confunde) |
| La página sigue tras un fallo | Se mandan trozos con la ventana cerrada, o se acumula `en_duda` sin que nadie lo vea |
| La página reintenta sola (o `js/api.js` por ella) | Un reintento que nadie pidió contra el ERP de producción |
| Se enseña mal el resultado | La persona cree creado lo que está en duda, o al revés |
| El cierre de la sección queda a medias | Guardias de F-035 en rojo |

**Rigor `critico`**, como la ficha. RED con traza pegada; cobertura de lo
cambiado (la puerta de `init.sh` dice lo que mide en el front); mutación:
`harness.mutacion` cubre los `.py` (aquí no hay `.py` de producción: su
informe lo dirá y se justifica por escrito) y, para `js/volcado.js` y las
guardias del HTML, **mutaciones a mano por familias** como F-035 y F-038, con
su traza.

## 1 · Dependencias y contrato consumido

- **F-059** `done`: mergeada en `dev`, desplegada el 2026-10-17 (`dev`
  `81049bc`) con la ventana cerrada y verificada en producción el 2026-10-19.
  La rama de F-040 sale de `dev` `f7f63da`, que ya la trae: esa es su **base
  fija** (se anota en `progress/impl_F-040.md`) *(conciliado 2026-10-27: ya
  no hace falta el merge previo del Bloque 1)*.
- **F-038**: `bandeja.html` y `js/revision.js` están en `dev` y publicados;
  la ficha está `blocked` a la espera de su T7 (verificación manual). Ver
  C-1.

El contrato **implementado** (conciliado 2026-10-27), sin reinterpretarlo.
Todas las respuestas de error son `{error, codigo}` más lo propio de cada
código; `js/api.js` lo deja en `ErrorApi.codigo`, `ErrorApi.http` y
`ErrorApi.detalle`.

- `GET /api/volcado?obra=` → 200 `{obra, partes_por_llamada, resumen:
  {aprobadas, en_duda, volcadas}, candidatas: [{incidencia_id, revision_id,
  estado, ultimo_volcado}]}`. `candidatas` son **todas** las de la obra (sin
  paginar; tope de lectura 10.000), en el orden de la bandeja; `estado` es el
  de la revisión (`aprobada` o `en_duda`); `ultimo_volcado` es el objeto
  `volcado` de R4 **sin** `volcado_por`. Errores: 400 `peticion_invalida`;
  409 `bandeja_demasiado_grande` (con `total`); 503
  `configuracion_de_volcado_invalida` o `base_de_datos_no_disponible`. No lee
  Sigrid.
- `POST /api/volcado/ensayo` con **exactamente** `{obra, usuario_oid,
  usuario_correo, incidencias}` (`incidencias`: de 1 a `partes_por_llamada`
  UUID distintos) → 200 `{ensayo_id, obra, caduca_at_utc, resumen:
  {previstos, idempotentes, rechazados, no_procesados, excluidas}, partes:
  [{incidencia_id, revision_id, referencia_externa, estado, motivo,
  sigrid_cod, envio}], excluidas: [{incidencia_id, motivo, sigrid_cod}]}`.
  `estado` ∈ `previsto | idempotente | rechazado | no_procesado`; `motivo`,
  un código (o nulo); `envio`, el parte tal cual se mandaría:
  `{referencia_externa, unidad_postventa, descripcion, [descripcion_larga],
  tipo, oficio, ubicacion, forma_comunicacion, intervinientes: [{oficio,
  proveedor, causante}]}`. **Si no queda nada que mandar**, 200 con
  `ensayo_id` y `caduca_at_utc` **nulos**, `partes` vacío y las excluidas.
  Errores: 400 `peticion_invalida`; 409 `usuario_sigrid_no_mapeado`,
  `usuario_sigrid_inexistente`, `volcado_rechazado_por_la_pasarela` (con
  `codigo_pasarela`), `bandeja_demasiado_grande`; 502 `ensayo_sin_respuesta`
  (repetir es inocuo); 503 configuración, base o un rechazo de la pasarela
  que es configuración de su dueño. **No mira la ventana** (D-4).
- `POST /api/volcado/volcar` con **exactamente** `{obra, ensayo_id,
  usuario_oid, usuario_correo, confirmado, incidencias}` (`confirmado`, el
  booleano `true`; `incidencias`: de 1 a `partes_por_llamada` objetos con
  **exactamente** `{incidencia_id, revision_id}`) → 200 `{llamada_id, obra,
  resumen: {creados, idempotentes, rechazados, no_procesados, sin_respuesta,
  excluidas}, partes: [{incidencia_id, referencia_externa, estado, motivo,
  sigrid_cod}], excluidas, avisos: [{incidencia_id, referencia_externa,
  sigrid_cod_anterior, sigrid_cod}]}`. `estado` ∈ `creado | idempotente |
  rechazado | no_procesado | sin_respuesta`. Si todo queda excluido, 200 con
  `llamada_id` nulo y `partes` vacío. Errores:
  - 400 `peticion_invalida` (antes de construir nada);
  - 409 `ensayo_no_valido` (con `motivo`: `no_existe`, `de_otra_obra`,
    `de_otra_persona`, `caducado`), `usuario_sigrid_no_mapeado`,
    `usuario_sigrid_inexistente`, `volcado_rechazado_por_la_pasarela` (con
    `codigo_pasarela`: nada escrito, los partes quedan `no_procesado`);
  - 502 `ensayo_sin_respuesta` (el login no se pudo verificar: **antes** de
    escribir) o `volcado_sin_respuesta` (con `en_duda`: la lista de
    `incidencia_id` que quedan en duda; reintentar es seguro);
  - 500 `volcado_sin_traza` (Sigrid respondió y no se pudo guardar: las del
    trozo quedan en duda);
  - 503 `volcado_deshabilitado` (entorno o ventana), configuración, base, o
    un rechazo de la pasarela que es configuración de su dueño.
- `GET /api/revision`: `estado` puede ser `volcada` o `en_duda`, cada
  incidencia trae `volcado` (F-059 R4) y la respuesta trae el `catalogo` de la
  obra (`unidades: [{codigo, nombre}]`, `oficios: [{codigo, nombre, grupo}]`,
  `pares: [{oficio_codigo, proveedor_codigo, proveedor_nombre}]`), que es de
  donde salen los nombres del ensayo (R51).

**Tiempos (conciliado 2026-10-27).** El front aborta a los 40 s
(`TIMEOUT_PETICION_MS`), el proxy de la Static Web App corta a los 45 y el
backend concede 35 s a cada llamada a la pasarela (`SIGRID_TIMEOUT_S`), más la
lectura del login, que sí reintenta. Un volcado puede, por tanto, quedarse
**sin respuesta del servicio** en el front y seguir escribiendo detrás: el
panel lo trata como «no se sabe» (R53.2).

## 2 · El panel en `bandeja.html` (D-2)

Identidad Ruesma (`rs-*`), una `<section class="rs-panel">` **debajo del
resumen de la obra y encima de la lista de incidencias**, dentro de `<main>` y
del único `x-data="appRevision()"`, visible con una obra cargada:

1. **Rótulo y entradilla**: «Volcado a Sigrid. Solo lo aprobado se vuelca.
   Primero se ensaya: el ensayo no crea nada.»
2. **Recuentos** de `GET /api/volcado`: aprobadas, en duda, volcadas, y
   «N candidatas, en M trozos de `partes_por_llamada`».
3. **«Ver qué se crearía en Sigrid»** (R51): un ensayo tras otro con barra de
   progreso («trozo k de M»); tabla única con unidad, oficio y proveedor
   (nombres del `catalogo`; sin nombre, el código del `envio`), ubicación,
   descripción, tipo, estado y motivo; las excluidas aparte. Si un ensayo
   falla, la serie para y lo dice (R51).
4. **Cuenta atrás** hasta la caducidad más temprana de los ensayos (30 min).
5. **«Volcar N partes a Sigrid»** (R52): primer clic abre la confirmación con
   el texto «Se van a crear N partes en el ERP de producción de la obra X.
   Escribe N para confirmar»; segundo clic con el número exacto manda.
6. **Progreso y resultado** (R53, R59): «trozo k de M»; creados (con su
   `RS…`), ya creados, rechazados con su motivo, no procesados, excluidas, en
   duda, sin mandar y avisos de posible duplicado; si hubo algún creado,
   «Quedan en SAT en Sigrid: pásalos a PTE a mano». Ante un fallo, el panel
   para y dice qué hacer; **«Volver a ensayar»** es el único reintento, y lo
   pulsa una persona: ensaya lo que el panel devuelve como candidato en ese
   momento, que es como se reanuda (R53.6).

**La guarda de salida (R55, conciliado 2026-10-27).** El único `<script>` en
línea de `bandeja.html` (F-038 R13) pregunta hoy con
`Revision.hayEdicionSinGuardar(Alpine.$data(raiz))`; se amplía para preguntar
también con `Volcado.hayVolcadoEnMarcha(...)` del mismo componente. Sigue
siendo **un** `addEventListener("beforeunload")` que solo lee.

## 3 · `js/volcado.js`

### 3.1 · Lo puro

Con `node --test` (`tests_js/volcado.test.js`, que el patrón
`tests_js/*.test.js` de `test_f007_js.py` recoge solo). Exporta `Volcado` como
`revision.js` (`window.Volcado` y `module.exports`) y **reutiliza**
`Revision.textoMotivoVolcado` (cargado antes en la página; en node,
`require("./revision.js")`) para los códigos de §8.9.

| Función | Qué hace | R |
|---|---|---|
| `trocear(ids, n)` | Grupos de `n` en orden, sin perder ni repetir | R51 |
| `cuerpoDeEnsayo(obra, ids, identidad)` | `{obra, usuario_oid, usuario_correo, incidencias}`, sin `confirmado` | R51 |
| `cuerpoDeVolcado(ensayo, identidad)` | **El único** `confirmado: true`; solo los `previsto`, cada uno `{incidencia_id, revision_id}` de su parte del ensayo; `null` si no hay ninguno | R52 |
| `juntarEnsayos(respuestas, catalogo)` | Una tabla (con los nombres del catálogo) y un resumen; N; la caducidad más temprana de los que tienen `ensayo_id`; si hubo algún `idempotente` | R51, R52, R53.5 |
| `puedeVolcar(estado, ahora)` | ≥ 1 previsto, todos los ensayos en 200, sin caducar, sin petición en vuelo | R52, R56 |
| `confirmacionValida(tecleado, n)` | El número exacto de partes (D-12) | R52 |
| `caducado(ensayo, ahora)` | El ensayo de un trozo ya no vale (`caduca_at_utc`) | R53.1 |
| `siguientePaso(resultado)` | Seguir o **parar**: para ante cualquier no-200, sin respuesta del servicio o un 200 con `resumen.sin_respuesta` > 0; el mensaje según §3.2 | R51, R53 |
| `juntarVolcados(respuestas, fallo, sinMandar)` | Creados, ya creados, rechazados, no procesados, excluidas, en duda (de los `sin_respuesta`, de `en_duda` del 502, del trozo del 500 o del corte) y sin mandar; los avisos | R53.4 |
| `avisoDePte(resumen)` | El aviso de R59 si hay algún `creado` | R59 |
| `textoExclusion(codigo)`, `textoEnsayoNoValido(causa)`, `textoError(codigo)`, `etiquetaParte(estado)` | Castellano para cada código propio de F-059 (R54); los de §8.9, por `Revision.textoMotivoVolcado` | R54 |
| `hayVolcadoEnMarcha(estado)` | La guarda de salida | R55 |

### 3.2 · Qué dice el panel al parar (conciliado 2026-10-27)

| Respuesta | En ensayo | En volcado (el trozo) |
|---|---|---|
| 400 `peticion_invalida` | Error de la página: recarga | Igual; nada escrito |
| 409 `ensayo_no_valido` (`caducado`, `de_otra_persona`, `no_existe`, `de_otra_obra`) | — | Nada escrito; vuelve a ensayar |
| 409 `usuario_sigrid_no_mapeado` / `usuario_sigrid_inexistente` | El texto del servicio (alta con `infra/07_alta_usuario_sigrid.ps1`) | Igual; nada escrito |
| 409/503 `volcado_rechazado_por_la_pasarela` | El texto de `codigo_pasarela` (`textoMotivoVolcado`) | Igual; nada escrito, el trozo `no_procesado` |
| 409 `bandeja_demasiado_grande` | Con `total` | — |
| 502 `ensayo_sin_respuesta` | Sigrid no respondió a tiempo; repetir es inocuo | Nada escrito (antes de escribir) |
| 502 `volcado_sin_respuesta` | — | Las de `en_duda`, en duda; volver a ensayar y volcar es seguro |
| 500 `volcado_sin_traza` | — | Las del trozo, en duda; avisa a sistemas |
| 503 `volcado_deshabilitado` | — | **La ventana del volcado está cerrada**; nada escrito |
| 503 otros (configuración, base) | Avisa a sistemas | Igual; nada escrito |
| Sin respuesta del servicio | Repetir es inocuo | **No se sabe**: las del trozo, en duda hasta volver a leer |
| 200 con algún `sin_respuesta` | — | Esas, en duda; para |

### 3.3 · Cómo se monta en la página (conciliado 2026-10-27)

- **Un solo `x-data`.** La guardia R70 de F-035 (`_x_data` de
  `tests/test_f035_paginas.py`) exige un único elemento con `x-data` por
  página real, así que el panel **no** lleva un `x-data` propio: su estado
  vive bajo una sola clave, `volcado`, del componente `appRevision`, y sus
  métodos se mezclan en él (`Volcado.conPanel(app, {api})`, o equivalente) de
  modo que `this` sea el proxy de Alpine y alcance `obraCargada`, `usuario`,
  `catalogo` y `cargar()`. Nada guarda en un cierre el objeto crudo: lo que
  se escribiera ahí no lo vería Alpine.
- **En `js/revision.js`**, lo mínimo: la fábrica `appRevision()` llama a
  `Volcado.conPanel` si `window.Volcado` existe, y `cargar()` avisa al panel
  tras una carga buena para que pida `GET /api/volcado` (R50). Ni las tablas
  ni la presentación de F-038 cambian.
- **En `js/api.js`**, tres funciones: `volcadoPanel(obra)` (`GET`, con
  `mensajeDelServicio`), `volcadoEnsayo(cuerpo)` y `volcadoVolcar(cuerpo)`
  (`POST` JSON, con `mensajeDelServicio` y **`sinReintentos: true`**: por
  defecto `peticion` reintenta dos veces un 502 o un corte, que en un volcado
  sería el reintento que R53 prohíbe). Mismo `TIMEOUT_PETICION_MS` (40 s). Sin
  `mensajeDelServicio`, un 503 saldría con el texto de la puerta de archivar.
- **La identidad** es la de `api.identidad()` (`identidadDe`, `{usuarioOid,
  correo}`), la que ya guarda `appRevision` en `usuario`; no se lee otra.
  **Nada sale sin un clic** (R56).

## 4 · El cierre en el portal (R57)

Como D-11 de F-038: un solo commit que quita los restos de F-040 de la maqueta
y pone el enlace a `bandeja.html` y **también** F-040 `done` en
`harness/features.json` *(conciliado 2026-10-27, lo que hay hoy en `dev`)*:

- `index.html#/bandeja`: el `<div class="rs-panel">` «Volcado a Sigrid» con
  sus tres botones `data-placeholder="F-040"`, sus dos resultados de ejemplo y
  sus pendientes; en su lugar, el enlace «Volcar a Sigrid» a `bandeja.html`.
- `js/maqueta_datos.js`: de `volcado`, `ficha`, `dryRun`, `hecho`,
  `pendientes` y `catalogos.estados`; `catalogos.tipos`, `formas` y `oficios`
  **se mudan** (p. ej. a `MaquetaDatos.catalogos`, sin ficha), porque
  `tipo()`, `forma()` y `oficio()` de `js/portal_app.js` los usan en las
  secciones de incidencias. La fila «Volcado a Sigrid» de `datamart.filas`
  (`fichas: ["F-040"]`) **no** es un resto de F-040: es del bloque de F-048
  y se queda.
- `js/portal.js`: las tres entradas de `PLACEHOLDERS`, `resumenVolcado` y
  `etiquetaEstadoVolcado` (solo las usa el panel).
- `js/portal_app.js`: `estadoVolcado`, `resumenVolcado` y la lectura de
  `datos.volcado.catalogos`, que pasa a la nueva ubicación.
- Los tests que solo servían a eso, citados con el porqué:
  `tests_js/portal.test.js` (R8 del volcado, R40, el recuento de reglas
  `[data-estado]` de R57, «cinco de volcado»), `tests_js/maqueta_datos.test.js`
  (`volcado: "F-040"`, el dry-run y el volcado hecho, los pendientes de F-040).

Lo prepara el implementer por encargo del líder, tras la verificación (Bloque
2) y el APROBADO; review corta de ese commit; si falla, se revierte entero.
**Orden con F-038**: si F-038 no está `done` cuando se cierre F-040, la sección
`bandeja` pasa a `parcial` por F-040 y no por F-038 (R62 de F-035), y ese
commit arrastra la marca de la barra en todas las páginas reales; es la
pregunta C-1.

## 5 · Ficheros

**A crear** (`services/postventa-front/`): `js/volcado.js`,
`tests_js/volcado.test.js`, `tests/test_f040_front.py`.

**A modificar** (conciliado 2026-10-27):

- `bandeja.html`: la sección del panel; `<script src="js/volcado.js">`
  **detrás** de `js/revision.js` (los propios tienen que cerrar el `<body>`,
  `problemas_de_carga` de `test_f036_front.py`); la guarda de salida ampliada.
- `js/api.js`: las tres funciones de §3.3.
- `js/revision.js`: solo la composición de `appRevision()` y el aviso de
  `cargar()` (§3.3).
- `README.md` del front y `docs/ARCHITECTURE.md` (R58).
- Tests de F-036/F-038 que el panel obliga a cambiar, cada uno citado con el
  porqué en el commit:
  - `tests/test_f038_front.py`: `SCRIPTS_DE_BANDEJA` pasa de cuatro a cinco
    (`test_f038_r1_carga_sus_cuatro_scripts_y_monta_app_revision`);
    `test_f038_r13_un_solo_beforeunload_que_solo_lee` acepta la guarda
    ampliada (sigue siendo una, sin red ni almacenamiento);
    `test_f038_r15_la_pagina_no_habla_con_nadie_por_su_cuenta` mira también
    `js/volcado.js`.
  - `tests_js/revision.test.js`: el recorrido de `bandeja.html` (Bloque 1
    bis) evalúa las expresiones del panel contra un componente que ya lleva
    `volcado`.
  - `tests_js/api.test.js`: los endpoints pasan de 20 a 23 (`LOS_ENDPOINTS`).
- En el cierre (R57): `index.html`, `js/maqueta_datos.js`, `js/portal.js`,
  `js/portal_app.js`, `harness/features.json` y los tests de §4; y, en el
  repositorio `azure-apps`, `postventa_incidencias.md` (R58).

**No se toca**: `services/postventa-api/` entero (es F-059); `infra/*`;
`js/importacion.js`, `js/oficios.js`, `js/guarda_salida.js`, `js/app.js`,
`js/pipeline.js`, `js/config.js` (los 40 s no se suben: lo explica el propio
fichero); `staticwebapp.config.json`; `dev_server.py`; las tablas y la
presentación del volcado de `js/revision.js` (F-038 R21).

## 6 · Lo que esta ficha hereda de las decisiones del 2026-10-07

| Id | Qué significa aquí |
|---|---|
| D-1 | Solo front; F-059 ya está `done` |
| D-2 | Panel en `bandeja.html`, no una sexta página |
| D-6 | El troceo lo hace esta página, de uno en uno, sin reintento automático (tampoco el de `js/api.js`) |
| D-12 | Segundo clic y teclear el número de partes |
| D-13 | Sin `cod` provisionales en el ensayo (el backend ya no los devuelve) |
| Q-1 | El tipo que se enseña es siempre `0002` |
| Q-3 | Aviso de que los partes quedan en SAT y Posventa los pasa a PTE a mano (R59) |
| Q-4 | La verificación con escritura real es en la obra 0626 (en cuestión: C-6) |
| Q-7 | Cualquiera del grupo con login de Sigrid ve el panel activo |
| Q-8 | El primer volcado masivo de la 0677 no es parte de esta ficha (en cuestión: C-2) |

## 7 · Tests

| R | Dónde | Lo que fija además de lo obvio |
|---|---|---|
| R50 | pytest | El panel en `bandeja.html`, dentro del único `x-data`; `js/volcado.js` cargado detrás de `js/revision.js`; solo lee al cargar |
| R51 | node | `trocear` con `n` 1, 5 y mayor que la lista, y 285 entre 5 = 57; `juntarEnsayos` con excluidas, con un ensayo sin `ensayo_id` y con nombres que faltan en el catálogo; la serie para en el primer ensayo no-200 o sin respuesta |
| R52 | node, pytest | Un solo `confirmado: true` en todo el front; `cuerpoDeVolcado` sin los no `previsto` y `null` sin ninguno; `puedeVolcar` con caducado, sin previstos, con un ensayo no-200 y con petición en vuelo; `confirmacionValida` con `N`, `N±1`, vacío y texto |
| R53 | node | Se para en 400, 409, 500, 502, 503, sin respuesta del servicio y en un 200 con `sin_respuesta`; con el ensayo del trozo caducado no se manda; no se pide el trozo siguiente; `volcadoEnsayo` y `volcadoVolcar` no se reintentan ante un 502 ni un corte (con el `fetch` doble de `api.test.js`); los avisos llegan al resultado; tras parar se relee el panel |
| R54 | node | Un texto para **cada** motivo de exclusión, cada causa de `ensayo_no_valido` y cada `codigo` de error de §3.2; §8.9 por `Revision.textoMotivoVolcado`; desconocido → el código tal cual |
| R55, R56 | pytest, node | Sin `console.*` ni `localStorage`/`sessionStorage` con identidad; acciones solo en `@click`; la guarda de salida, una, pregunta con un volcado en marcha y no sin él |
| R57 | raíz | Las guardias de F-035 con F-040 `done`; F-039 y F-043 con restos; los catálogos de la maqueta siguen sirviendo a `tipo()`, `forma()` y `oficio()` |
| R58 | pytest | README y `ARCHITECTURE.md` cuentan el panel |
| R59 | node | El aviso solo con algún `creado` |

## 8 · Riesgos y alternativas descartadas

1. **Página propia `volcado.html`**: descartada (D-2): una sexta página toca
   todas las guardias de F-035, y el volcado es lo que sigue a aprobar.
2. **Reintento automático de un trozo**: descartado: el reintento es seguro
   en Sigrid, pero lo pide una persona (mismo criterio que el cierre).
3. **Mandar los trozos en paralelo**: descartado: multiplica la carga sobre la
   pasarela y hace ilegible el resultado; de uno en uno es lo que se mide.
4. **Un `x-data` propio para el panel** *(conciliado 2026-10-27)*: descartado:
   rompe la guardia R70 de F-035 en la página; el estado va bajo `volcado`.
5. **Riesgo: una obra grande tarda** *(conciliado 2026-10-27, con el volumen
   real)*: la VILLA 15 son unas 285 incidencias, 57 trozos. Con lo medido en
   F-059 (ensayo 1,2–5,8 s con un parte; volcado 1,8 s), del orden de 3–10 min
   de ensayos y otro tanto de volcados; el peor caso por trozo es el corte de
   40 s, que con 57 trozos serían 38 min. La barra de progreso y la guarda de
   salida lo hacen visible; el ajuste de `N` es Q-8.
6. **Riesgo: el ensayo caduca** mientras se lee o a mitad del volcado: el
   trozo 1 es el primero que caduca y el que antes se vuelca, así que el
   margen es, más o menos, lo que duran los ensayos más lo que se tarda en
   leer y confirmar. La cuenta atrás lo enseña, el panel no manda un trozo
   caducado (R53.1) y, si se le escapa, el backend devuelve 409
   `ensayo_no_valido` `caducado`; en los dos casos se vuelve a ensayar lo que
   queda, que ya no incluye lo volcado.
7. **Riesgo: el arranque en frío** de `sigrid-api` (35 s el 2026-10-19): el
   primer ensayo tras un rato parado puede dar 502 `ensayo_sin_respuesta` o
   el corte de 40 s; ensayar otra vez es inocuo y el panel lo dice.
8. **Riesgo: un volcado sin respuesta del servicio sigue escribiendo** detrás
   (§1, «Tiempos»): el panel para, lo trata como en duda y relee; la
   referencia `PVI-` hace que volver a ensayar y volcar no duplique.

## 9 · Conciliación 2026-10-27 (resumen)

| § | Qué cambió | Por qué (código de `dev`) |
|---|---|---|
| 1 | Contrato con los cuerpos exactos, `resumen` por modo, ensayo y volcado vacíos (ids nulos), todos los códigos de error con su HTTP, `avisos`, `catalogo` | `interface_adapters/api/volcado.py`, `CODIGOS_DEL_VOLCADO` y `HTTP_DEL_VOLCADO` de `function_app.py`, `revision.py` |
| 1 | Sin merge previo: la rama sale de un `dev` con F-059 | `59ce4c9` desde `f7f63da` |
| 1 | Tiempos: 40 s del front, 35 s de la pasarela | `js/config.js`, `SIGRID_TIMEOUT_S` |
| 2, 3.3 | Panel bajo `volcado` del único `x-data`; guarda de salida ampliada | `_x_data` (F-035 R70); `test_f038_r13_…` |
| 3.1 | `cuerpoDeVolcado` → `null` sin previstos; `caducado`; `siguientePaso` con corte y `sin_respuesta`; avisos; textos propios separados de §8.9 | `_lista`, `interpretar_respuesta`, `avisos`, `Revision.textoMotivoVolcado` |
| 3.2 | Tabla de paradas por código | `function_app.py` |
| 3.3 | `sinReintentos` y `mensajeDelServicio` en las tres funciones | `peticion` y `clasificar` de `js/api.js` |
| 4 | Los catálogos de la maqueta se quedan; lista exacta de restos | `js/portal_app.js`, `index.html`, `js/portal.js` |
| 5 | `js/revision.js` casi no se toca (R54 ya es F-038 R21); tests de F-036/F-038 nombrados | `js/revision.js`, `tests/test_f038_front.py`, `tests_js/revision.test.js`, `tests_js/api.test.js` |
| 8 | Volumen real y riesgos de caducidad, arranque en frío y corte | `progress/impl_F-059.md` (T25) |
