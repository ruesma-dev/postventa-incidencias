<!-- specs/F-040-volcado-sigrid/design.md -->
# F-040 · Volcar a Sigrid las incidencias aprobadas (el panel de volcado) — Diseño técnico

> **Aprobado por el humano el 2026-10-07.** Es el **tramo B** de la spec
> conjunta, partida por D-1: esta ficha es solo `services/postventa-front`.
> El backend, su contrato y todas las decisiones de escritura en el ERP son
> **F-059** (`specs/F-059-volcado-sigrid-backend/design.md`, sobre todo §3,
> §4, §11 y §20).

## 0 · Dónde está el riesgo

La puerta de verdad (qué se escribe, cuándo, y que no se duplique) es del
backend, F-059. Lo que esta página puede romper:

| Si falla… | Consecuencia |
|---|---|
| Un volcado sale sin clic, dos veces, o sin haber enseñado el ensayo | Se crean en el ERP partes que nadie miró (el backend exige ensayo de la misma persona, pero confunde) |
| La página sigue tras un fallo | Se mandan trozos con la ventana cerrada, o se acumula `en_duda` sin que nadie lo vea |
| La página reintenta sola | Un reintento que nadie pidió contra el ERP de producción |
| Se enseña mal el resultado | La persona cree creado lo que está en duda, o al revés |
| El cierre de la sección queda a medias | Guardias de F-035 en rojo |

**Rigor `critico`**, como la ficha. RED con traza pegada; cobertura de lo
cambiado (la puerta de `init.sh` dice lo que mide en el front); mutación:
`harness.mutacion` cubre los `.py` (aquí no hay `.py` de producción: su
informe lo dirá y se justifica por escrito) y, para `js/volcado.js` y las
guardias del HTML, **mutaciones a mano por familias** como F-035 y F-038, con
su traza.

## 1 · Dependencias

- **F-059** `done`, mergeada en `dev`, desplegada y verificada en producción
  (su Bloque 6). La rama de F-040 trae ese `dev` (merge) y ese merge es la
  **base fija** (se anota en `progress/impl_F-040.md`).
- **F-038** `done`: existe `bandeja.html` con `js/revision.js`.

El contrato consumido, sin reinterpretarlo (F-059 design §11):

- `GET /api/volcado?obra=` → `{obra, partes_por_llamada, resumen: {aprobadas,
  en_duda, volcadas}, candidatas: [{incidencia_id, revision_id, estado,
  ultimo_volcado}]}`.
- `POST /api/volcado/ensayo` `{obra, usuario_oid, usuario_correo,
  incidencias}` → `{ensayo_id, obra, caduca_at_utc, resumen, partes: [{…,
  estado, motivo, sigrid_cod, envio}], excluidas}`.
- `POST /api/volcado/volcar` `{obra, ensayo_id, usuario_oid, usuario_correo,
  confirmado: true, incidencias: [{incidencia_id, revision_id}]}` →
  `{llamada_id, resumen, partes, excluidas, avisos}`; errores 400, 409
  (`ensayo_no_valido`, login, pasarela), 502 `volcado_sin_respuesta` (con
  `en_duda`), 500 `volcado_sin_traza`, 503 (`volcado_deshabilitado`, …).
- `GET /api/revision`: `estado` puede ser `volcada` o `en_duda` y cada
  incidencia trae `volcado` (F-059 R4).

## 2 · El panel en `bandeja.html` (D-2)

Identidad Ruesma (`rs-*`), debajo del resumen de la bandeja y encima de la
lista:

1. **Rótulo y entradilla**: «Volcado a Sigrid. Solo lo aprobado se vuelca.
   Primero se ensaya: el ensayo no crea nada.»
2. **Recuentos** de `GET /api/volcado`: aprobadas, en duda, volcadas.
3. **«Ver qué se crearía en Sigrid»** (R51): trozos de `partes_por_llamada`,
   un ensayo tras otro con barra de progreso; tabla única con unidad, oficio y
   proveedor (nombres de la bandeja ya cargada; códigos del `envio`),
   ubicación, descripción, tipo, estado y motivo; las excluidas aparte.
4. **Cuenta atrás** hasta la caducidad más temprana de los ensayos (30 min).
5. **«Volcar N partes a Sigrid»** (R52): primer clic abre la confirmación con
   el texto «Se van a crear N partes en el ERP de producción de la obra X.
   Escribe N para confirmar»; segundo clic con el número exacto manda.
6. **Progreso y resultado** (R53, R59): creados (con su `RS…`), ya creados,
   rechazados con su motivo, no procesados, en duda y sin mandar; si hubo
   algún creado, «Quedan en SAT en Sigrid: pásalos a PTE a mano». Ante un
   fallo, el panel para y dice qué hacer; **«Volver a ensayar»** es el único
   reintento, y lo pulsa una persona.

## 3 · `js/volcado.js`

Lógica pura, con `node --test` (`tests_js/volcado.test.js`):

| Función | Qué hace | R |
|---|---|---|
| `trocear(ids, n)` | Grupos de `n` en orden, sin perder ni repetir | R51 |
| `cuerpoDeEnsayo(obra, ids, identidad)` | Sin `confirmado` | R51 |
| `cuerpoDeVolcado(ensayo, identidad)` | **El único** `confirmado: true`; solo los `previsto`, con su `revision_id` | R52 |
| `juntarEnsayos(respuestas)` | Una tabla y un resumen; la caducidad más temprana | R51, R52 |
| `puedeVolcar(estado, ahora)` | ≥ 1 previsto, todos los ensayos en 200, sin caducar, sin petición en vuelo | R52, R56 |
| `confirmacionValida(tecleado, n)` | El número exacto de partes (D-12) | R52 |
| `siguientePaso(respuesta)` | Seguir o **parar** ante cualquier no-200; el mensaje según el código (503 ventana cerrada, 502 en duda, 409 ensayo caducado…) | R53 |
| `juntarVolcados(respuestas, sinMandar)` | Creados, ya creados, rechazados, no procesados, en duda y sin mandar | R53 |
| `avisoDePte(resumen)` | El aviso de R59 si hay algún `creado` | R59 |
| `textoMotivo(codigo)`, `etiquetaEstado(estado)` | Castellano para cada código de §8.9 y propio de F-059 | R54 |
| `hayVolcadoEnMarcha(estado)` | El `beforeunload` | R55 |

La identidad es la de `identidadDe` de `js/api.js` (`{usuarioOid, correo}`);
no se escribe otra. Tres funciones nuevas en `js/api.js`: `volcadoPanel(obra)`,
`volcadoEnsayo(cuerpo)`, `volcadoVolcar(cuerpo)`, con el tiempo de petición de
siempre (40 s). El componente `crearAppVolcado({api})` solo guarda estado y
delega en lo puro. **Nada sale sin un clic** (R56).

En `js/revision.js` (de F-038), las etiquetas de `volcada` y `en_duda`, la
línea «Volcada como RS… por <correo> el <fecha>» y los filtros nuevos (R54).

## 4 · El cierre en el portal (R57)

Como D-11 de F-038: un solo commit que quita los restos de F-040 de la maqueta
(`index.html#/bandeja`: el panel de volcado; `js/maqueta_datos.js`:
`volcado`; `js/portal.js`: las tres entradas de `PLACEHOLDERS` y lo que solo
les servía; `js/portal_app.js`: lo que lea `datos.volcado`), pone el enlace a
`bandeja.html` y **también** F-040 `done` en `harness/features.json`. Lo
prepara el implementer por encargo del líder, tras la verificación (Bloque 2)
y el APROBADO; review corta de ese commit; si falla, se revierte entero.

## 5 · Ficheros

**A crear** (`services/postventa-front/`): `js/volcado.js`,
`tests_js/volcado.test.js`, `tests/test_f040_front.py`.

**A modificar**: `bandeja.html` (el panel y el `beforeunload`), `js/api.js`
(tres funciones), `js/revision.js` (R54), `README.md` (R58); en el cierre,
`index.html`, `js/maqueta_datos.js`, `js/portal.js`, `js/portal_app.js`,
`harness/features.json` y los tests de F-035/F-036/F-038 que cambien, cada uno
citado con el porqué.

**No se toca**: `services/postventa-api/` entero (es F-059); `infra/*`;
`js/importacion.js`, `js/oficios.js`, `js/guarda_salida.js`, `js/app.js`,
`js/pipeline.js`; `staticwebapp.config.json`; `dev_server.py`.

## 6 · Lo que esta ficha hereda de las decisiones del 2026-10-07

| Id | Qué significa aquí |
|---|---|
| D-1 | Solo front; bloqueada por F-059 |
| D-2 | Panel en `bandeja.html`, no una sexta página |
| D-6 | El troceo lo hace esta página, de uno en uno, sin reintento automático |
| D-12 | Segundo clic y teclear el número de partes |
| D-13 | Sin `cod` provisionales en el ensayo |
| Q-1 | El tipo que se enseña es siempre `0002` |
| Q-3 | Aviso de que los partes quedan en SAT y Posventa los pasa a PTE a mano (R59) |
| Q-4 | La verificación con escritura real es en la obra 0626 |
| Q-7 | Cualquiera del grupo con login de Sigrid ve el panel activo |
| Q-8 | El primer volcado masivo de la 0677 no es parte de esta ficha |

## 7 · Tests

| R | Dónde | Lo que fija además de lo obvio |
|---|---|---|
| R50 | pytest | El panel en `bandeja.html`; su componente; solo lee al cargar |
| R51 | node | `trocear` con `n` 1, 5 y mayor que la lista; `juntarEnsayos` con excluidas |
| R52 | node, pytest | Un solo `confirmado: true` en todo el front; `cuerpoDeVolcado` sin los no `previsto`; `puedeVolcar` con caducado, sin previstos, con un ensayo no-200 y con petición en vuelo; `confirmacionValida` con `N`, `N±1`, vacío y texto |
| R53 | node | Se para en 400, 409, 500, 502 y 503; no se pide el trozo siguiente; nada se reintenta solo |
| R54 | node | Un texto para **cada** código de §8.9 y propio; desconocido → el código tal cual |
| R55, R56 | pytest | Sin `console.*` ni `localStorage`/`sessionStorage` con identidad; acciones solo en `@click`; `beforeunload` |
| R57 | raíz | Las guardias de F-035 con F-040 `done`; F-039 y F-043 con restos |
| R59 | node | El aviso solo con algún `creado` |

## 8 · Riesgos y alternativas descartadas

1. **Página propia `volcado.html`**: descartada (D-2): una sexta página toca
   todas las guardias de F-035, y el volcado es lo que sigue a aprobar.
2. **Reintento automático de un trozo**: descartado: el reintento es seguro
   en Sigrid, pero lo pide una persona (mismo criterio que el cierre).
3. **Mandar los trozos en paralelo**: descartado: multiplica la carga sobre la
   pasarela y hace ilegible el resultado; de uno en uno es lo que se mide.
4. **Riesgo: una obra grande tarda** (k trozos × hasta 40 s): la barra de
   progreso y el `beforeunload` lo hacen visible; el ajuste de `N` es Q-8.
5. **Riesgo: el ensayo caduca** mientras se lee: la cuenta atrás lo enseña y
   el backend devuelve 409 `ensayo_no_valido`; se vuelve a ensayar.
