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
> §9 los resume. Las decisiones que la conciliación ponía en cuestión eran
> C-1 a C-6 de `progress/spec_F-040.md`.
>
> **Respuestas del humano aplicadas el 2026-10-28** (§10): «Registrar»
> sincroniza con Sigrid (F-065) antes de ensayar (§1.1, §2, §3), recuento por
> unidad, Bloque 3 tras F-038 `done`, T5 en la 0626, sin volcado de la VILLA
> 15 en la ficha.
>
> **Conciliado con el contrato implementado de F-065 el 2026-10-31** (T0, base
> fija `f97ec6e`): §1, §1.1, §2, §3.1–§3.3, §5, §7 y §8 citan la ruta, la
> forma y los errores reales, con fichero y línea; §11 lo resume. Lo que
> tocaría una decisión aprobada se preguntó como **P-1 a P-3**
> (`progress/spec_F-040.md`); **respuesta del humano 2026-10-31**: las tres
> como se recomendaron, aplicadas y marcadas «(P-n, respuesta del humano
> 2026-10-31)».

## 0 · Dónde está el riesgo

La puerta de verdad (qué se escribe, cuándo, y que no se duplique) es del
backend, F-059. Lo que esta página puede romper:

| Si falla… | Consecuencia |
|---|---|
| Un volcado sale sin clic, dos veces, o sin haber enseñado el ensayo | Se crean en el ERP partes que nadie miró (el backend exige ensayo de la misma persona, pero confunde) |
| Se ensaya sin haber sincronizado, o se incluye lo que choca sin el segundo clic *(2026-10-28)* | Se duplica en Sigrid lo que Posventa ya dio de alta a mano (la guarda del ensayo de F-065 es la segunda defensa, no la única) |
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
  La rama de F-040 sale de `dev` `f7f63da`, que ya la trae.
- **F-065** *(2026-10-28, C-4; conciliado 2026-10-31)*: `done`, mergeada en
  `dev` (`7cc0bbb`) y desplegada el 2026-10-31 desde `ed590bd`. La rama de
  F-040 trae ese `dev` en el merge `f97ec6e`, su **base fija**
  (`progress/impl_F-040.md`); §1.1 es su contrato implementado. Su T-A18
  (aplazada por el humano el 2026-10-31) la recoge esta ficha (`tasks.md`
  T5 bis, P-3, respuesta del humano 2026-10-31: aparte, en la 0677, solo
  ensayos, y el cierre no la espera).
- **F-038**: `bandeja.html` y `js/revision.js` están en `dev` y publicados;
  la ficha está `blocked` a la espera de su T7 (verificación manual). C-1
  (2026-10-28): los Bloques 1 y 2 no la esperan; el Bloque 3 sí.

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
- *(F-065, conciliado 2026-10-31)* El ensayo admite además
  `conflictos_confirmados`, su 200 gana el bloque `sigrid`, sus `excluidas`
  dos motivos y sus errores tres códigos: §1.1. `GET /api/volcado` y
  `POST /api/volcado/volcar` **no cambian** (R49 de F-065).

**Tiempos (conciliado 2026-10-27).** El front aborta a los 40 s
(`TIMEOUT_PETICION_MS`), el proxy de la Static Web App corta a los 45 y el
backend concede 35 s a cada llamada a la pasarela (`SIGRID_TIMEOUT_S`), más la
lectura del login, que sí reintenta. Un volcado puede, por tanto, quedarse
**sin respuesta del servicio** en el front y seguir escribiendo detrás: el
panel lo trata como «no se sabe» (R53.2).

### 1.1 · El contrato de F-065 que consume el panel (conciliado 2026-10-31)

El **implementado** en la base fija `f97ec6e`, sin reinterpretarlo. Todas
las rutas, en `services/postventa-api/`.

**La sincronización: `GET /api/revision/sigrid?obra=`** (`function_app.py`
l. 2074–2119; handler `interface_adapters/api/sigrid_bandeja.py`). Solo lee:
una lectura de la base y como mucho una de Sigrid (R3 de F-065). Todas sus
respuestas, también las de error, con `Cache-Control: no-store` (l.
2063–2071). Cualquier parámetro que no sea `obra` se ignora.

- **200** · `{obra, leido_at_utc, criterio, reclamaciones, hallazgos,
  incidencias, resumen, volcado}` (`_cuerpo`, l. 236–252). Lo que usa el
  panel:
  - `volcado` (`_volcado`, l. 324–347): `{candidatas, por_veredicto,
    por_unidad, veredictos}`. `veredictos`, uno por candidata (`aprobada` o
    `en_duda`), en el orden de la bandeja: `{incidencia_id, unidad_codigo,
    estado, veredicto, sigrid_cods}`, con la unidad y el estado **vigentes** y
    **todos** sus códigos (sin el tope de 10 de los hallazgos).
    `por_veredicto` y cada `por_unidad[<unidad_codigo>]` llevan **siempre** las
    cuatro claves `va`, `se_enlaza`, `ya_existe`, `choca`, en ese orden
    (`_por_veredicto`, l. 350–352); `por_unidad`, solo las unidades de las
    candidatas, por código.
  - `reclamaciones` (`_reclamacion`, l. 255–270): `{cod, estado, fecha,
    unidad_codigo, ubicacion, oficio_codigo, oficio_nombre, tipo_codigo,
    tipo_nombre, descripcion, referencia, incidencia_id, ficha}`; el panel las
    busca por `cod` para enseñar con qué choca o qué ya existe, y **no** usa
    `ficha` (datos personales, R33 de F-065).
  - `hallazgos` (`_hallazgo`, l. 273–283): `{tipo, severidad, incidencia_id,
    sigrid_cod, sigrid_cods, guardado_cod, criterios, parecido}`; del `coincide`
    de una incidencia con un código, `criterios` y `parecido` dicen **por qué**
    choca. Como mucho 10 `coincide` por incidencia (R18 de F-065): si un código
    de `sigrid_cods` no tiene hallazgo, el panel enseña la reclamación sin el
    porqué.
- **Los veredictos** (`domain/models/sigrid_bandeja.py` l. 127–137 y
  `_veredicto`, l. 697–713; R41 de F-065), por precedencia: `choca` si su
  emparejada por `PVI-` (la de código mayor) está en `NPR` o en un estado
  desconocido o vacío, con solo ese código; `se_enlaza` si la emparejada está
  en `PTE`, `SAT`, `TER` o `CER`; `ya_existe` si un par con los dos criterios
  es de una abierta (`SAT`/`PTE`); `choca` si hay otro par de conflicto con
  una abierta; `va` en lo demás. En el panel: **va** = `va` + `se_enlaza`
  (P-1, respuesta del humano 2026-10-31), **ya existe** = `ya_existe`, **choca** = `choca`. La emparejada de
  una incidencia es la reclamación de `reclamaciones` cuyo `incidencia_id` es
  el suyo: así distingue el panel el `choca` por un parte anulado del `choca`
  por criterios.
- **Errores** (l. 2096–2118):
  - **400** `{error, codigo: "peticion_invalida"}`: la obra no vale
    (`_error_de_revision`, l. 1642–1663);
  - **409** `{error, codigo: "bandeja_demasiado_grande", total}` (más de
    10.000, sin leer Sigrid); `{error, codigo: "reclamaciones_sin_verificar",
    filas}` (l. 2102–2107: techo o `truncated`, nada cruzado); `{error,
    codigo: "obra_ambigua"}` (`_rechazo_de_obra`, l. 1335–1341);
  - **503** `{error}` **sin `codigo`** (`_sin_sigrid_o_sin_base`, l.
    1344–1361): Sigrid, su configuración, el entorno o la base; el texto dice
    que se puede reintentar más tarde.
- **Tiempo** (`progress/impl_F-065.md`, T-A15, 10 cargas de la 0677 tras
  publicar): total p50 ≈ 0,67 s, máximo 4,70 s; 1.310.511 bytes. Cabe en los
  40 s del front.

**La guarda del ensayo: `POST /api/volcado/ensayo`** (cambios de F-065 sobre
el contrato de §1; `interface_adapters/api/volcado.py` l. 231–301):

- **Cuerpo**: las cuatro claves de F-059 y, **opcional**,
  `conflictos_confirmados: [{incidencia_id, sigrid_cods}]` (l. 238–250,
  461–504): cada `incidencia_id`, una de las `incidencias` del cuerpo y una
  sola vez; `sigrid_cods`, de 1 a 50 códigos distintos con la forma
  `RS<aa>.<mm>/<4 cifras>`. Mal formada → **400** `peticion_invalida` antes
  de construir nada. Sin la clave, lista vacía.
- **Qué hace** (`application/pipelines/guarda_sigrid.py` l. 96–172; F-065
  `design.md` §15.7): si la selección de F-059 deja algo que mandar, **una**
  lectura de Sigrid de las unidades de lo que se manda (sin datos
  personales), el mismo veredicto, y: `ya_existe` → excluida
  **`duplicada_en_sigrid`** con su primer código en `sigrid_cod`; `choca` con
  algún código **no** confirmado → excluida **`conflicto_sin_confirmar`** con
  el primero sin confirmar; `choca` con todos confirmados, `se_enlaza` y `va`
  → se mandan. Una confirmación de algo que ya no choca se ignora (y se cuenta
  en el log). **Relee Sigrid en cada ensayo**: no hay identificador de
  sincronización ni caducidad suya (S-4); lo que cambió entre la
  sincronización y el ensayo sale como exclusión. Si no queda nada que mandar,
  la respuesta de «nada que mandar» de F-059 (`ensayo_id` nulo), sin login ni
  lote.
- **200**: el de §1 más `sigrid` (`_sigrid_de`, l. 285–301): `{leido_at_utc,
  reclamaciones_leidas, veredictos: [{incidencia_id, veredicto, sigrid_cods,
  confirmada}]}`, o `null` si la guarda no leyó.
- **Errores nuevos** (`function_app.py` `CODIGOS_DEL_VOLCADO` l. 1892–1895,
  `HTTP_DEL_VOLCADO` l. 1913–1915, `_error_del_volcado` l. 1958–1959), con
  **nada** guardado, ni login, ni lote: **503** `sigrid_no_disponible`;
  **409** `reclamaciones_sin_verificar` (con `filas`); **409** `obra_ambigua`.
- **Diferencia escrita entre la ruta y la guarda** (`docs/INTEGRACION.md` l.
  319–325): la ruta lee la obra entera y la guarda solo las unidades que se
  mandan; con una referencia `PVI-` en **otra** unidad pueden diferir, y ese
  caso lo para la pasarela (`rechazado`, `referencia_en_conflicto`), que el
  panel ya enseña como rechazado con su motivo (§8.9, `textoMotivoVolcado`).
- **La línea `F-065 guarda del ensayo`** (`guarda_sigrid.py` l. 185–223): una
  por lectura con recuentos (`va`, `se_enlaza`, `ya_existe`, `choca`,
  `duplicada_en_sigrid`, `conflicto_sin_confirmar`, `con_conflicto_confirmado`,
  `confirmaciones_sobrantes`, `segundos`) y una por incidencia mandada con un
  conflicto confirmado, con **cuántos** códigos. Nunca un código `RS` ni un
  texto. Es lo que comprueba T-A18 (`tasks.md` T5 bis).

**Observación, no del panel**: la docstring de la ruta (`function_app.py` l.
2081–2082) lista la respuesta 200 **sin** `volcado`, que sí sale
(`sigrid_bandeja.py` l. 251). No se toca aquí (`services/postventa-api` es de
F-065); va al líder.

## 2 · El panel en `bandeja.html` (D-2)

Identidad Ruesma (`rs-*`), una `<section class="rs-panel">` **debajo del
resumen de la obra y encima de la lista de incidencias**, dentro de `<main>` y
del único `x-data="appRevision()"`, visible con una obra cargada:

1. **Rótulo y entradilla**: «Volcado a Sigrid. Solo lo aprobado se vuelca.
   Primero se mira lo que ya hay en Sigrid y después se ensaya: ni lo uno ni
   lo otro crea nada.» *(2026-10-28)*
2. **Recuentos** de `GET /api/volcado`: aprobadas, en duda, volcadas, y
   «N candidatas, en M trozos de `partes_por_llamada`».
3. **«Registrar»** (R60, 2026-10-28), el único botón de entrada. Paso 1: la
   sincronización, `GET /api/revision/sigrid` (§1.1). Paso 2: tres grupos
   —**va** (las `se_enlaza`, marcadas «se enlaza con RS…» y sumadas al recuento de va, P-1, respuesta del
   humano 2026-10-31), **ya
   existe** (con sus códigos de Sigrid), **choca** (cada reclamación con la
   que choca: estado, unidad, ubicación, oficio y descripción, y el porqué;
   o «su parte RS… está anulado en Sigrid»)— con el recuento por unidad de
   cada uno (R61) y, aparte, las candidatas de `GET /api/volcado` que la
   sincronización no nombra; lo que ya existe no tiene botón; lo que choca,
   una casilla **por incidencia** para incluirla, que es el **segundo clic**
   de R62 (P-2, respuesta del humano 2026-10-31: sin «todas las de la
   unidad») y viaja en `conflictos_confirmados` con todos sus códigos.
   Paso 3: **«Ensayar lo que va»** (y lo incluido).
4. **El ensayo** (R51): un ensayo tras otro con barra de progreso («trozo k
   de M»); tabla única con unidad, oficio y proveedor (nombres del
   `catalogo`; sin nombre, el código del `envio`), ubicación, descripción,
   tipo, estado y motivo; las excluidas aparte; el recuento por unidad de lo
   que se crearía. Si un ensayo falla, la serie para y lo dice (R51).
5. **Cuenta atrás** hasta la caducidad más temprana de los ensayos (30 min).
6. **«Volcar N partes a Sigrid»** (R52): primer clic abre la confirmación con
   el texto «Se van a crear N partes en el ERP de producción de la obra X:
   n₁ de <unidad 1>, n₂ de <unidad 2>… Escribe N para confirmar»; segundo
   clic con el número exacto manda.
7. **Progreso y resultado** (R53, R59): «trozo k de M»; creados (con su
   `RS…`), ya creados, rechazados con su motivo, no procesados, excluidas
   (también lo que ya existía y lo que chocaba sin incluir), en duda, sin
   mandar y avisos de posible duplicado; si hubo algún creado, «Quedan en SAT
   en Sigrid: pásalos a PTE a mano». Ante un fallo, el panel para y dice qué
   hacer; **«Volver a registrar»** es el único reintento, y lo pulsa una
   persona: repite desde la sincronización con lo que el panel devuelve como
   candidato en ese momento, que es como se reanuda (R53.6).

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
| `agruparSincronizacion(candidatas, respuesta, catalogo)` *(conciliado 2026-10-31)* | Con `respuesta` el 200 de `GET /api/revision/sigrid` (§1.1) y `candidatas` las de `GET /api/volcado`: cada fila de `respuesta.volcado.veredictos` en **va** (`va` y `se_enlaza`, esta marcada con su código, P-1, respuesta del humano 2026-10-31), **ya existe** (`ya_existe`) o **choca** (`choca`), en el orden de la respuesta; a cada código, su reclamación de `respuesta.reclamaciones` **sin `ficha`** y, si es `choca`, el porqué (`anulada`: la reclamación tiene el `incidencia_id` de la fila; si no, `criterios` y `parecido` de su `coincide` de `hallazgos`, o nada si no viajó); el recuento por unidad de cada grupo, de `volcado.por_unidad`; y `sinSincronizar`, las `candidatas` que los veredictos no nombran. Un veredicto desconocido, en **choca** sin casilla (no se puede incluir) | R61, R51 |
| `paraEnsayar(grupos, incluidas)` *(conciliado 2026-10-31)* | Los `incidencia_id` de **va** más los de **choca** que están en `incluidas`, en el orden de la sincronización; nunca **ya existe** ni `sinSincronizar` | R62, R51 |
| `confirmadosDelTrozo(ids, grupos, incluidas)` *(conciliado 2026-10-31)* | Para el cuerpo del ensayo: `[{incidencia_id, sigrid_cods}]` de las incluidas que van en ese trozo, con **todos** los `sigrid_cods` de su veredicto; lista vacía si ninguna | R62 |
| `puedeEnsayar(estado)` *(2026-10-28)* | Sincronización en 200, ≥ 1 para ensayar, sin petición en vuelo | R60, R56 |
| `recuentoPorUnidad(filas, catalogo)` *(2026-10-28)* | Cuántas por unidad, con su nombre (sin nombre, el código), para el ensayo y la confirmación (en el paso 2 sale de `por_unidad`) | R61, R51, R52 |
| `trocear(ids, n)` | Grupos de `n` en orden, sin perder ni repetir | R51 |
| `cuerpoDeEnsayo(obra, ids, identidad, confirmados)` *(conciliado 2026-10-31)* | `{obra, usuario_oid, usuario_correo, incidencias}`, sin `confirmado`, y `conflictos_confirmados` **solo** si `confirmados` no está vacía | R51, R62 |
| `excluidasDeLaGuarda(respuestas, grupos)` *(conciliado 2026-10-31)* | Las excluidas `duplicada_en_sigrid` y `conflicto_sin_confirmar` de los ensayos; marca «cambió desde la sincronización» las que iban en **va**, o las incluidas cuya `sigrid_cod` no estaba entre sus códigos confirmados; con alguna marcada, el panel ofrece «Volver a registrar» | R62 |
| `cuerpoDeVolcado(ensayo, identidad)` | **El único** `confirmado: true`; solo los `previsto`, cada uno `{incidencia_id, revision_id}` de su parte del ensayo; `null` si no hay ninguno | R52 |
| `juntarEnsayos(respuestas, catalogo)` | Una tabla (con los nombres del catálogo) y un resumen; N; la caducidad más temprana de los que tienen `ensayo_id`; si hubo algún `idempotente` | R51, R52, R53.5 |
| `puedeVolcar(estado, ahora)` | ≥ 1 previsto, todos los ensayos en 200, sin caducar, sin petición en vuelo | R52, R56 |
| `confirmacionValida(tecleado, n)` | El número exacto de partes (D-12) | R52 |
| `caducado(ensayo, ahora)` | El ensayo de un trozo ya no vale (`caduca_at_utc`) | R53.1 |
| `siguientePaso(resultado)` | Seguir o **parar**: para ante cualquier no-200, sin respuesta del servicio o un 200 con `resumen.sin_respuesta` > 0; el mensaje según §3.2 | R51, R53 |
| `juntarVolcados(respuestas, fallo, sinMandar)` | Creados, ya creados, rechazados, no procesados, excluidas, en duda (de los `sin_respuesta`, de `en_duda` del 502, del trozo del 500 o del corte) y sin mandar; los avisos | R53.4 |
| `avisoDePte(resumen)` | El aviso de R59 si hay algún `creado` | R59 |
| `textoExclusion(codigo)`, `textoEnsayoNoValido(causa)`, `textoError(codigo)`, `etiquetaParte(estado)`, `textoVeredicto(veredicto)`, `textoPorque(choque)` | Castellano para cada código propio de F-059 (R54), para los de F-065 (`duplicada_en_sigrid`, `conflicto_sin_confirmar`; `sigrid_no_disponible`, `reclamaciones_sin_verificar`, `obra_ambigua`; los cuatro veredictos; los criterios `misma_unidad_oficio_ubicacion` y `misma_unidad_descripcion_parecida`) y para el 503 sin `codigo` de la sincronización; los de §8.9, por `Revision.textoMotivoVolcado` | R54, R61 |
| `hayVolcadoEnMarcha(estado)` | La guarda de salida | R55 |

*(Conciliado 2026-10-31.)* Las firmas de la sincronización quedan cerradas
contra §1.1. **Qué se ensaya lo decide la sincronización**, no
`GET /api/volcado`: una candidata aprobada después de sincronizar no tiene
veredicto, así que no se ensaya y se pide «Volver a registrar»; una que tiene
veredicto y ya no es candidata la excluye el ensayo (`no_es_candidata`, F-059).
El panel guarda de la respuesta de la sincronización **solo** lo que enseña
(veredictos, recuentos y las reclamaciones citadas, sin `ficha`); el resto del
cuerpo no se conserva.

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

*(Conciliado 2026-10-31.)* La sincronización (`GET /api/revision/sigrid`, §1.1)
para **antes del paso 2**, sin ensayar ni dejar ensayar:

| Respuesta de la sincronización | Qué dice el panel |
|---|---|
| 400 `peticion_invalida` | Error de la página: recarga |
| 409 `bandeja_demasiado_grande` | Con `total` |
| 409 `reclamaciones_sin_verificar` | Sigrid devolvió demasiadas reclamaciones (`filas`) o cortadas: no se puede saber qué hay; avisa a sistemas |
| 409 `obra_ambigua` | Hay más de una obra con ese código en Sigrid: lo tiene que mirar una persona |
| 503 (sin `codigo`) | El texto del servicio (`mensajeDelServicio`): sin Sigrid o sin base, nada escrito, se puede volver a registrar más tarde |
| Otro no-200 (p. ej. el 504 del proxy) o sin respuesta del servicio | No se ha podido mirar Sigrid; volver a registrar es inocuo (solo lee) |

Y el ensayo, por la guarda de F-065:

| Respuesta del ensayo | Qué dice el panel |
|---|---|
| 503 `sigrid_no_disponible` | Sigrid no responde: no se ha ensayado nada (ni guardado); la serie para; volver a registrar más tarde |
| 409 `reclamaciones_sin_verificar` (con `filas`) / 409 `obra_ambigua` | Como en la sincronización; la serie para, nada guardado |
| 400 `peticion_invalida` (también un `conflictos_confirmados` mal formado) | Error de la página: recarga |
| 200 con excluidas `duplicada_en_sigrid` / `conflicto_sin_confirmar` | No es un fallo: la serie sigue; salen en las excluidas con su texto y su `sigrid_cod`; si alguna «cambió desde la sincronización» (`excluidasDeLaGuarda`), propone «Volver a registrar» |

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
  *(2026-10-28; conciliado 2026-10-31)* Y una cuarta,
  `revisionSigrid(obra)`: `GET /api/revision/sigrid?obra=` (con `conObra`,
  como `revision`), con `mensajeDelServicio` (el 503 llega sin `codigo` y su
  texto es el que vale) y **`sinReintentos: true`**: es una lectura, pero
  pesada (1,3 MB en la 0677) y con datos personales; la repite la persona con
  otro «Registrar». `volcadoEnsayo(cuerpo)` manda `conflictos_confirmados` tal
  cual lo compone `cuerpoDeEnsayo`.
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
**Orden con F-038** (C-1, decidido el 2026-10-28): este commit va **después**
de que F-038 esté `done`. Si fuera antes, la sección `bandeja` pasaría a
`parcial` por F-040 y no por F-038 (R62 de F-035) y arrastraría la marca de la
barra en todas las páginas reales, que es trabajo del cierre de F-038.

## 5 · Ficheros

**A crear** (`services/postventa-front/`): `js/volcado.js`,
`tests_js/volcado.test.js`, `tests/test_f040_front.py`.

**A modificar** (conciliado 2026-10-27):

- `bandeja.html`: la sección del panel; `<script src="js/volcado.js">`
  **detrás** de `js/revision.js` (los propios tienen que cerrar el `<body>`,
  `problemas_de_carga` de `test_f036_front.py`); la guarda de salida ampliada.
- `js/api.js`: las tres funciones de §3.3 y `revisionSigrid` (conciliado
  2026-10-31).
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
  - `tests_js/api.test.js`: los endpoints pasan de **20 a 24**
    (`LOS_ENDPOINTS`, l. 206–231 en la base fija `f97ec6e`: F-065 no tocó el
    front y F-064 no está en `dev`): `volcadoPanel`, `volcadoEnsayo`,
    `volcadoVolcar` y `revisionSigrid` (conciliado 2026-10-31).
- En el cierre (R57): `index.html`, `js/maqueta_datos.js`, `js/portal.js`,
  `js/portal_app.js`, `harness/features.json` y los tests de §4; y, en el
  repositorio `azure-apps`, `postventa_incidencias.md` (R58).

**No se toca**: `services/postventa-api/` entero (es F-059 y, la
sincronización y la guarda del ensayo, F-065); `infra/*`;
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
| Q-4 | La verificación con escritura real es en la obra 0626 (confirmado el 2026-10-28, C-6) |
| Q-7 | Cualquiera del grupo con login de Sigrid ve el panel activo |
| Q-8 | El primer volcado masivo de la 0677 no es parte de esta ficha: lo hará el humano con el panel operativo (confirmado el 2026-10-28, C-2) |

Y las del 2026-10-28 (C-1…C-6, `requirements.md` §5): «Registrar» sincroniza
con Sigrid antes de ensayar y F-040 depende de F-065 (C-4); recuento por
unidad (C-3); Bloque 3 tras F-038 `done` (C-1); aprobar en bloque fuera
(C-5).

## 7 · Tests

| R | Dónde | Lo que fija además de lo obvio |
|---|---|---|
| R50 | pytest | El panel en `bandeja.html`, dentro del único `x-data`; `js/volcado.js` cargado detrás de `js/revision.js`; solo lee al cargar; «Registrar» es el único botón de entrada |
| R60 | node | «Registrar» pide `GET /api/revision/sigrid?obra=` y nada más, una vez; sin una sincronización en 200 no se puede ensayar (`puedeEnsayar`); para antes del ensayo con 400, cada 409 de §3.2, el 503 sin `codigo`, otro no-200 y un corte; `revisionSigrid` no se reintenta ante un 502 ni un corte; el orden sincronizar → enseñar → ensayar, con el `api` doble y respuestas con la forma de §1.1 (datos ficticios) |
| R61 | node | `agruparSincronizacion`: los cuatro veredictos en tres grupos (`se_enlaza` en va, marcado); el recuento de `por_unidad` con nombres del catálogo y, sin nombre, el código; el porqué de un `choca` por `NPR` (emparejada) y por criterios, y sin hallazgo; `sinSincronizar`; un veredicto desconocido sin casilla; ninguna clave de `ficha` en lo que guarda el panel |
| R62 | node, pytest | `paraEnsayar` nunca lleva ya existe ni `sinSincronizar`; lo que choca solo con su casilla; `confirmadosDelTrozo` con todos los códigos y solo las del trozo; `cuerpoDeEnsayo` sin `conflictos_confirmados` si no hay ninguna; `excluidasDeLaGuarda` marca lo que cambió; el texto del segundo clic en un `choca` por `NPR` dice que enlaza con el parte anulado; ningún botón incluye lo que ya existe |
| R51 | node | `trocear` con `n` 1, 5 y mayor que la lista, y 285 entre 5 = 57; `juntarEnsayos` con excluidas, con un ensayo sin `ensayo_id` y con nombres que faltan en el catálogo; la serie para en el primer ensayo no-200 o sin respuesta |
| R52 | node, pytest | Un solo `confirmado: true` en todo el front; `cuerpoDeVolcado` sin los no `previsto` y `null` sin ninguno; `puedeVolcar` con caducado, sin previstos, con un ensayo no-200 y con petición en vuelo; `confirmacionValida` con `N`, `N±1`, vacío y texto; el texto de la confirmación con el recuento por unidad |
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
9. **Riesgo: la sincronización de una obra grande tarda** *(2026-10-28;
   conciliado 2026-10-31)*: medido tras publicar F-065 (T-A15), la 0677 da
   p50 ≈ 0,67 s y máximo 4,70 s, con 1,3 MB; cabe en los 40 s del front. Si
   no cabe un día, el panel para y lo dice (R60) y la persona vuelve a
   registrar.
10. **Riesgo: Sigrid cambia entre la sincronización y el volcado**
    *(2026-10-28; conciliado 2026-10-31)*: la sincronización no caduca porque
    la guarda **relee Sigrid en cada ensayo** (§1.1); lo que cambió sale como
    exclusión y el panel propone volver a registrar. Entre el ensayo y el
    volcado (hasta 30 min) `volcar` no relee: riesgo aceptado en F-065 (S-6,
    `design.md` §15.8).
11. **Alternativa descartada: ensayar sin sincronizar** (como estaba el
    2026-10-27): descartada por el humano el 2026-10-28 (C-4): el volcado de
    F-059 no ve lo dado de alta a mano y lo duplicaría.
12. **Riesgo: la ruta y la guarda difieren** *(conciliado 2026-10-31)* con
    una referencia `PVI-` en otra unidad (`docs/INTEGRACION.md` l. 319–325):
    el panel puede enseñar «va» y el ensayo «se enlaza», o al revés; la
    pasarela lo para (`referencia_en_conflicto`) y el panel lo enseña como
    rechazado con su motivo.

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

## 10 · Respuestas del humano del 2026-10-28 (resumen)

| § | Qué cambió | Por qué |
|---|---|---|
| 1, 1.1 | F-040 depende de F-065, que va antes; la base fija pasa a ser el merge del `dev` con F-065; tabla de lo que el panel espera de su contrato (sustituida el 2026-10-31 por el contrato implementado, §11) | C-4 |
| 1, 4 | El Bloque 3 va tras F-038 `done`; los Bloques 1 y 2 no la esperan | C-1 |
| 2 | «Registrar» como único botón de entrada: sincronizar → va / ya existe / choca con recuento por unidad → ensayar; «Volver a registrar» como reanudación; recuento por unidad en el ensayo y en la confirmación | C-4, C-3 |
| 3.1 | `agruparSincronizacion`, `paraEnsayar`, `puedeEnsayar`, `recuentoPorUnidad`; firmas a cerrar con F-065 | C-4, C-3 |
| 3.2, 3.3 | Paradas de la sincronización y de la guarda del ensayo; una cuarta función en `js/api.js` | C-4 |
| 6 | Q-4 (0626) y Q-8 (sin volcado masivo en la ficha) confirmadas | C-6, C-2 |
| 7 | Tests de R60–R62 y del recuento en la confirmación | C-4, C-3 |
| 8 | Riesgos de la sincronización (tiempo, Sigrid que cambia) y la alternativa descartada | C-4 |

Lo pendiente para cuando F-065 estuviera en `dev` (§1.1, §3.1, §3.2 y §3.3) se
hizo el 2026-10-31: §11.

## 11 · Conciliación con F-065 (2026-10-31, T0)

Contra la base fija `f97ec6e` (`dev` `7cc0bbb`, F-065 `done`, desplegada desde
`ed590bd`).

| § | Qué cambió | De dónde (fichero:línea) |
|---|---|---|
| 1 | F-065 `done` y su base fija; el ensayo gana clave, bloque, motivos y errores; `GET /api/volcado` y `volcar`, sin cambios | `interface_adapters/api/volcado.py` 231–301; F-065 R49 |
| 1.1 | La tabla de necesidades, sustituida por el contrato implementado: la ruta, su 200 (`volcado`, `reclamaciones`, `hallazgos`), los veredictos y su precedencia, los errores (el 503 sin `codigo`), el tiempo medido; la guarda del ensayo (cuerpo, exclusiones, `sigrid`, errores, la línea de log) y la diferencia ruta/guarda | `function_app.py` 1335–1361, 1642–1663, 1877–1961, 2063–2119; `sigrid_bandeja.py` 236–352; `domain/models/sigrid_bandeja.py` 127–137, 697–713; `guarda_sigrid.py` 96–223; `docs/INTEGRACION.md` 292–353; `progress/impl_F-065.md` T-A15 |
| 2 | El paso 2 con `se_enlaza` en va (P-1), el porqué del choque, las no sincronizadas y la casilla por incidencia (P-2); respuesta del humano 2026-10-31 | §1.1 |
| 3.1 | `agruparSincronizacion`, `paraEnsayar`, `cuerpoDeEnsayo` con firma cerrada; nuevas `confirmadosDelTrozo`, `excluidasDeLaGuarda`, `textoVeredicto`, `textoPorque`; qué se ensaya lo decide la sincronización; sin `ficha` | §1.1 |
| 3.2 | Paradas de la sincronización y del ensayo por la guarda, código a código | `function_app.py` 2096–2118, 1892–1915 |
| 3.3 | `revisionSigrid`, con `mensajeDelServicio` y `sinReintentos` | `js/api.js` 280–320 (`peticion`) |
| 5 | `LOS_ENDPOINTS` de 20 a 24 | `tests_js/api.test.js` 206–231 |
| 7 | Tests de R60–R62 contra la forma real | §1.1 |
| 8 | Riesgos 9 y 10 con lo medido y la relectura de la guarda; riesgo 12 nuevo | `progress/impl_F-065.md` T-A15; F-065 §15.8 |

Preguntas P-1 a P-3 (`progress/spec_F-040.md`): **respuesta del humano
2026-10-31**, las tres como se recomendaron, aplicadas en §1, §1.1, §2 y §3.1
y en `tasks.md` (T5 bis, T6).
