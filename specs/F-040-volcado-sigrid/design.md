<!-- specs/F-040-volcado-sigrid/design.md -->
# F-040 · Volcar a Sigrid las incidencias aprobadas (el panel de volcado) — Diseño técnico

> **Rigor: `critico`.** Disparador **2** de «Niveles de rigor» (`CHECKPOINTS.md`): es el botón que **escribe en el
> ERP de producción** (`POST /api/volcado/volcar` → `POST /api/sigrid/partes-reclamacion` de `sigrid-api`); y toca
> datos personales de clientes en memoria (la respuesta de la sincronización, disparador 3).
> Aprobado el 2026-10-07 (tramo B, D-1: solo `services/postventa-front`); conciliado el 2026-10-27 (C-1..C-6) y el
> 2026-10-31 con F-065 (P-1..P-3), todas respondidas por el humano.
> **Puesta al día del 2026-11-18** (§11): condensado para la puerta TAMAÑO; lo nuevo y lo corregido va marcado
> **[E-1118]**. El diseño íntegro anterior, con fichero y línea de cada contrato (sus §1, §1.1, §9–§11):
> `git show 4b1eb21:specs/F-040-volcado-sigrid/design.md`. Decisiones abiertas: §12.

## 0 · Dónde está el riesgo

La puerta de verdad (qué se escribe, cuándo, sin duplicar) es del backend (F-059, F-065). Lo que esta página rompe:

| Si falla… | Consecuencia |
|---|---|
| Un volcado sale sin clic, dos veces o sin enseñar el ensayo | Partes en el ERP que nadie miró |
| Se ensaya sin sincronizar, o lo que choca sin su segundo clic | Duplicado de lo dado de alta a mano (la guarda de F-065 es la segunda defensa) |
| La página sigue tras un fallo, o reintenta sola (o `js/api.js` por ella) | Trozos con la ventana cerrada, `en_duda` sin ver, reintentos que nadie pidió |
| Se enseña mal el resultado o el tipo **[E-1118]** | Se cree creado lo que está en duda, o se cree que va como 0002 lo que va como 0003 |
| El cierre de la sección queda a medias | Guardias de F-035 en rojo |

RED con traza pegada; cobertura N/A con motivo (la puerta mide `.py` y aquí no hay); mutación de `js/volcado.js`,
`js/revision.js` y el HTML **a mano por familias**, como F-035 y F-038, con cada mutante y su test asesino.

## 1 · Dependencias y contrato consumido

- **F-059** `done` (desplegada el 2026-10-17, verificada el 2026-10-19 en la 0626). **F-065** `done` (desplegada el
  2026-10-31). **F-038** `done` (2026-11-12, `dev` `eca6ae3`). **F-072** `done` (publicada el 2026-11-18, `dev`
  `a269341`) **[E-1118]**. La rama trae todo en el merge `4b1eb21`, nueva base fija (`progress/impl_F-040.md`; lo anterior, en `progress/impl_F-040_hasta_2026-11-05.md`, D-8).
- El contrato **implementado**, sin reinterpretarlo, con sus errores en §3.2: `docs/INTEGRACION.md` §1 («Con
  F-065») y §3 bis («Qué escribimos como PARTE NUEVO»); por campo y línea, la versión `4b1eb21` (§1, §1.1):
  - `GET /api/volcado?obra=` → `{partes_por_llamada, resumen, candidatas: [{incidencia_id, revision_id, estado,
    ultimo_volcado}]}`. `GET /api/revision/sigrid?obra=` → `{reclamaciones, hallazgos, volcado: {por_unidad,
    veredictos: [{incidencia_id, unidad_codigo, estado, veredicto, sigrid_cods}]}}`, `no-store` (0677: p50 0,67 s).
  - `POST /api/volcado/ensayo` `{obra, usuario_oid, usuario_correo, incidencias, [conflictos_confirmados]}` →
    `{ensayo_id, caduca_at_utc, resumen, partes: [{…, estado, motivo, sigrid_cod, envio}], excluidas, sigrid}`
    (sin nada que mandar, `ensayo_id` nulo). `POST /api/volcado/volcar` `{obra, ensayo_id, usuario_oid,
    usuario_correo, confirmado, incidencias: [{incidencia_id, revision_id}]}` → `{llamada_id, resumen, partes,
    excluidas, avisos}`.
  - `GET /api/revision` → `volcada`/`en_duda`, el objeto `volcado` y el `catalogo` (`unidades`, `oficios`, `pares`
    y **`listados`**, §1.1).
- **Tiempos**: el front corta a 40 s, el proxy a 45 y la pasarela tiene 35 s: un volcado puede quedar **sin
  respuesta** en el front y seguir escribiendo detrás (R53.2). **SQL**: ninguno (esta ficha no toca la base).

### 1.1 · Lo que F-072 cambia para el panel [E-1118]

| Dónde | Desde F-072 | Consecuencia en el front |
|---|---|---|
| `envio.tipo` del ensayo | El **tipo efectivo** (`tipo_reclamacion`, nulo → `0002`), no la constante | R63: etiqueta de `catalogo.listados`; fuera `TEXTO_TIPO` |
| `catalogo.listados` | Los tipos vigentes de `auxtrcp` como `{codigo, etiqueta}`, `<res> (<cod>)` (4 al medir: `0001`–`0004`) | La única fuente de etiquetas; el panel no lee `auxtrcp` |
| `valores.listado` | El tipo efectivo, **nunca nulo**; `null` al editar guarda `0002` | R67: la opción «Sin listado» sobra [D-3] |
| Motivos de la revisión | 10: `tipo_fuera_de_sigrid` (entre `proveedor_ambiguo` y `duplicada`) | R66; no es aprobable → nunca candidata nueva |
| Ensayo con un tipo de baja | La pasarela rechaza `tipo_no_valido`; el volcado no relee `auxtrcp` (F-072 R29) | R65: «No se crea» con qué hacer; no cuenta en N |
| `GET /api/volcado`, sincronización, `volcar` | **Sin cambios**: no traen el tipo | El tipo solo se conoce tras el ensayo (por eso R64 va en la confirmación) |

Lo verificado en producción por F-072 (T26, 2026-11-18): un ensayo de una aprobada con `0003` sale `previsto` con
`envio.tipo: "0003"`. Ninguna escritura real con un tipo ≠ `0002` todavía: es la que propone D-6 (T5.4).

## 2 · El panel en `bandeja.html` (D-2)

Una `<section class="rs-panel">` debajo del resumen y encima de la lista, dentro de `<main>` y del único `x-data`:
(1) rótulo y entradilla («Solo lo aprobado se vuelca. Primero se mira lo que ya hay en Sigrid y después se ensaya:
ni lo uno ni lo otro crea nada»); (2) recuentos de `GET /api/volcado` y «N candidatas, en M trozos»; (3)
**«Registrar»** (R60): tres grupos con recuento por unidad (R61), aparte las no sincronizadas, ya existe sin botón y
choca con su casilla (R62), y «Ensayar lo que va»; (4) el ensayo (R51): «trozo k de M», tabla con unidad, oficio,
proveedor, ubicación, descripción, **tipo con su etiqueta (R63)**, estado y motivo, excluidas aparte, recuento por
unidad (y **por tipo** si hay más de uno, R64 [D-2]); (5) cuenta atrás (30 min); (6) «Volcar N partes a Sigrid»
(R52), cuya confirmación dice «Se van a crear N partes en el ERP de producción de la obra X: n₁ de <unidad 1>…
[D-2: y n₁ PRIMER LISTADO POSTVENTA (0002), n₂ POST VENTA (0003)]. Escribe N»; (7) progreso y resultado (R53,
R59), con «Volver a registrar» como único reintento.

**Guarda de salida (R55)**: el único `<script>` en línea de `bandeja.html` (F-038 R13) pregunta también con
`Volcado.hayVolcadoEnMarcha(...)`; sigue siendo **un** `beforeunload` que solo lee.

## 3 · `js/volcado.js` y lo que toca de la página

### 3.1 · Lo puro (`tests_js/volcado.test.js`, `node --test`)

Exporta `Volcado` como `revision.js` y reutiliza `Revision.textoMotivoVolcado` para los códigos de §8.9.

| Función | Qué hace | R |
|---|---|---|
| `agruparSincronizacion(candidatas, respuesta, catalogo)` | Veredictos en va (con `se_enlaza` marcado) / ya existe / choca, en su orden; a cada código su reclamación sin `ficha` y el porqué de un `choca` (`anulada` o criterios y parecido); recuento de `por_unidad`; `sinSincronizar`; un veredicto desconocido, en choca sin casilla | R61, R51 |
| `paraEnsayar(grupos, incluidas)`, `confirmadosDelTrozo(ids, grupos, incluidas)`, `puedeEnsayar(estado)` | Va + choca con casilla, nunca ya existe ni `sinSincronizar`; `[{incidencia_id, sigrid_cods}]` del trozo; sincronización en 200, ≥ 1, nada en vuelo | R62, R60, R56 |
| `trocear(ids, n)`, `cuerpoDeEnsayo(obra, ids, identidad, confirmados)`, `excluidasDeLaGuarda(respuestas, grupos)` | Grupos de `n` sin perder ni repetir; el cuerpo, con `conflictos_confirmados` solo si hay; las excluidas de la guarda y «cambió desde la sincronización» | R51, R62 |
| `juntarEnsayos(respuestas, catalogo)` **[E-1118]** | Una tabla con nombres del catálogo **y el tipo con la etiqueta de `catalogo.listados`** (sin ella, el código); N; la caducidad más temprana; si hubo `idempotente` | R51, R63, R53.5 |
| `recuentoPorUnidad(filas, catalogo)`; **`recuentoPorTipo(filas, catalogo)` [E-1118, D-2]** | Cuántas por unidad / por tipo, con su nombre o etiqueta (sin ella, el código) | R51, R52, R64 |
| `cuerpoDeVolcado(ensayo, identidad)` | **El único** `confirmado: true`; solo los `previsto` con su `revision_id`; `null` sin ninguno | R52 |
| `puedeVolcar(estado, ahora)`, `confirmacionValida(tecleado, n)`, `caducado(ensayo, ahora)` | ≥ 1 previsto, todos en 200, sin caducar, nada en vuelo; el número exacto (D-12); el trozo ya no vale | R52, R53.1 |
| `siguientePaso(resultado)`, `juntarVolcados(respuestas, fallo, sinMandar)`, `avisoDePte(resumen)` | Seguir o parar (no-200, sin respuesta, `sin_respuesta`); el resultado acumulado con en duda y avisos; R59 | R53, R59 |
| `textoExclusion`, `textoEnsayoNoValido`, `textoError`, `etiquetaParte`, `textoVeredicto`, `textoPorque` | Castellano para cada código de F-059 y F-065 y el 503 sin `codigo`; §8.9 por `Revision.textoMotivoVolcado` | R54, R61 |
| `hayVolcadoEnMarcha(estado)` | La guarda de salida | R55 |

**Qué se ensaya lo decide la sincronización**, no `GET /api/volcado`. **[E-1118]** `TEXTO_TIPO` (la tabla fija de
`0002`, Q-1) se borra: la etiqueta sale de `catalogo.listados` (`nombreDeTipo(catalogo, codigo)`, privada).

### 3.2 · Qué dice el panel al parar

| Respuesta | En la sincronización | En un ensayo | En un volcado (el trozo) |
|---|---|---|---|
| 400 `peticion_invalida` | Error de la página: recarga | Igual | Igual; nada escrito |
| 409 `bandeja_demasiado_grande` / `reclamaciones_sin_verificar` / `obra_ambigua` | Con `total` / demasiadas o cortadas, avisa a sistemas / mírelo una persona | Igual; la serie para, nada guardado | — |
| 409 `usuario_sigrid_*`, `volcado_rechazado_por_la_pasarela` | — | El texto del servicio / de `codigo_pasarela` | Igual; nada escrito, `no_procesado` |
| 409 `ensayo_no_valido` (4 causas) | — | — | Nada escrito; vuelve a registrar |
| 502 `ensayo_sin_respuesta` | — | Repetir es inocuo | Nada escrito (antes de escribir) |
| 502 `volcado_sin_respuesta`; 500 `volcado_sin_traza` | — | — | Las de `en_duda` / las del trozo, en duda; repetir es seguro / avisa a sistemas |
| 503 `volcado_deshabilitado` | — | — | **La ventana del volcado está cerrada**; nada escrito |
| 503 `sigrid_no_disponible`; 503 sin `codigo`; otros 503 | El texto del servicio, nada escrito | Sigrid no responde: nada ensayado | Avisa a sistemas; nada escrito |
| Otro no-200 o sin respuesta del servicio | No se ha podido mirar Sigrid; repetir es inocuo | Repetir es inocuo | **No se sabe**: en duda hasta releer |
| 200 con `sin_respuesta` / con excluidas de la guarda | — | No es fallo: sigue y propone «Volver a registrar» | Esas, en duda; para |
| **[E-1118]** 200 con un `rechazado` `tipo_no_valido` | — | No es fallo: «No se crea», con qué hacer (R65) | Igual, si llegara (no cuenta en N) |

### 3.3 · Cómo se monta

- **Un solo `x-data`**: el estado bajo la clave `volcado` de `appRevision`, métodos mezclados con
  `Volcado.conPanel(app, {api})` (`this` = el proxy de Alpine); en `js/revision.js`, la composición y el aviso de
  `cargar()` (R50). La identidad, la de `api.identidad()`. Nada sale sin un clic (R56).
- **`js/api.js`**: `volcadoPanel(obra)` (lectura, reintenta lo transitorio), `volcadoEnsayo`, `volcadoVolcar` y
  `revisionSigrid`, estas tres con `mensajeDelServicio` y **`sinReintentos`**.

### 3.4 · Textos de Q-11 de F-072 y la miga [E-1118]

Q-11 de F-072 (humano, 2026-11-15) los deja a esta ficha. Por eso **se amplía lo que esta ficha toca de
`js/revision.js`** (antes, «solo la composición»), y solo en esto:

| Dónde | Hoy | Con F-040 | R |
|---|---|---|---|
| `js/revision.js` `MOTIVOS`, `TEXTO_MOTIVO`, cabecera de `presentarResumen` | 9 motivos; `tipo_fuera_de_sigrid` sale en crudo | 10, con su texto [D-1] | R66 |
| `js/revision.js` `TEXTO_MOTIVO_VOLCADO.tipo_no_valido` | «El tipo de reclamación no existe en Sigrid» | El texto de R65 [D-1] | R65 |
| `js/revision.js` `textoDeCampo("listado")` | «sin listado» si nulo | La etiqueta, o el código | R67 |
| `bandeja.html`, campo del formulario | «Listado», con `<option value="">Sin listado</option>` | «Listado (tipo de reclamación)» [D-1]; sin la opción en blanco y con la del tipo no vigente [D-3], de una función pura nueva `Revision.opcionesDeListado(catalogo, actual)` | R67 |
| `js/volcado.js` `TEXTO_TIPO` | `{"0002": "0002 PRIMER LISTADO POSTVENTA"}` | Fuera (§3.1) | R63 |
| `bandeja.html`, migas | `<a href="./#/bandeja">Bandeja de revisión</a>` | `<span aria-current="page">Bandeja de revisión</span>` (humano, 2026-11-05) | R68 |

## 4 · El cierre en el portal (R57)

Como D-11 de F-038: **un solo commit** que quita los restos de F-040 de la maqueta y pone F-040 `done` en
`harness/features.json`; review corta; si falla, se revierte entero. Va tras T5 y el APROBADO del Bloque 1 bis
(F-038 ya `done`: C-1 cumplida). Restos, contados en `4b1eb21`:
- `index.html#/bandeja`: el bloque `data-en-construccion="F-040"` (panel de ejemplo, tres botones, resultados y
  pendientes). **[E-1118, D-4]** Sin enlace nuevo: F-038 T8 dejó la tarjeta «Revisar la bandeja» a `bandeja.html`;
  su texto y el de la tarjeta 02 del inicio (ya «En producción») ganan «y volcar a Sigrid lo aprobado».
- `js/maqueta_datos.js`: de `volcado`, `ficha`, `dryRun`, `hecho`, `pendientes` y `catalogos.estados`;
  `catalogos.tipos`, `formas` y `oficios` **se mudan** (los usan `tipo()`, `forma()` y `oficio()` de
  `js/portal_app.js`); la fila «Volcado a Sigrid» de `datamart.filas` es de F-048 y se queda.
- `js/portal.js`: `bandeja.verVolcado`, `bandeja.volcar` y `bandeja.reintentarVolcado` de `PLACEHOLDERS`,
  `resumenVolcado`, `etiquetaEstadoVolcado` (y `"F-040"` de `TITULOS_FICHAS` si deja de usarse; la sección sigue
  `parcial` por F-039 y F-043). `js/portal_app.js`: `estadoVolcado`, `resumenVolcado`, `datos.volcado.catalogos`.
- Los tests que solo servían a eso (`tests_js/portal.test.js`, `tests_js/maqueta_datos.test.js`), citados.

## 5 · Ficheros

**Creados en el Bloque 1** (`services/postventa-front/`): `js/volcado.js`, `tests_js/volcado.test.js`,
`tests/test_f040_front.py`. **[E-1118]** Bloque 1 bis: `tests_js/f040_tipo.test.js` (R63–R67) o casos nuevos en
`volcado.test.js` y `revision.test.js`, a elección del implementer, con nombres `f040 R6n`.

**A modificar en el Bloque 1 bis [E-1118]**: `js/volcado.js` (§3.1), `js/revision.js` y `bandeja.html` (§3.4);
`tests_js/revision.test.js` (los «nueve motivos» de R4 y R5 de F-038 pasan a diez; el texto de `tipo_no_valido`),
`tests_js/volcado.test.js` (las filas con «0002 PRIMER LISTADO POSTVENTA»), `tests/test_f038_front.py`
(`MIGAS_DE_BANDEJA` con un solo enlace y la miga actual como `span`), cada aserción citada con el R que la sustituye.
**En el cierre (R57, R58)**: `index.html`, `js/maqueta_datos.js`, `js/portal.js`, `js/portal_app.js`,
`harness/features.json`, los tests de §4, `docs/ARCHITECTURE.md` (fuera «sin publicar todavía», l. ~1629),
`docs/INTEGRACION.md` (las frases de F-040 en futuro: l. 145, 160, 212, 599, 652, 2072–2076) y, en `azure-apps`,
`postventa_incidencias.md` (las mismas).

**No se toca**: `services/postventa-api/` entero (F-059, F-065, F-072); `infra/*`; `js/importacion.js`,
`js/oficios.js`, `js/guarda_salida.js`, `js/app.js`, `js/pipeline.js`, `js/config.js` (los 40 s no se suben);
`staticwebapp.config.json`; `dev_server.py`; de `js/revision.js`, todo lo que no nombra §3.4 (las tablas de F-038
R21 salvo `tipo_no_valido`); `importar.html` (su columna «Listado» ya la explica la plantilla de F-072).

## 6 · Decisiones heredadas

D-1 y D-2: solo front, panel en `bandeja.html`. D-6, D-12, D-13: troceo de uno en uno sin reintento; segundo clic
y teclear N; sin `cod` provisionales. ~~Q-1: el tipo es siempre `0002`~~ **[E-1118]** superada por F-072 (humano,
2026-11-05 y 2026-11-15): el tipo efectivo. Q-3: aviso de PTE a mano. Q-4/C-6: escritura de verificación en la
0626. Q-7: cualquiera de `posventa-usuarios` con login de Sigrid. Q-8/C-2: el volcado masivo no es de la ficha.
C-1: Bloque 3 tras F-038 `done` (cumplido). C-3: recuento por unidad. C-4: sincronizar antes de registrar. C-5:
aprobar en bloque fuera. P-1: `se_enlaza` en va. P-2: casilla por incidencia. P-3: T5 bis aparte, en la 0677, solo
ensayos; el cierre no la espera. Humano 2026-11-05: miga como texto (R68); tarjeta del inicio (hecha por F-038).

## 7 · Tests

| R | Dónde | Lo que fija además de lo obvio |
|---|---|---|
| R50, R56 | pytest | Panel dentro del único `x-data`; «Registrar» único botón de entrada; `js/volcado.js` tras `js/revision.js`; acciones solo en `@click` |
| R60–R62 | node, pytest | Orden sincronizar → enseñar → ensayar con el `api` doble; cada parada de §3.2; sin `ficha`; ningún botón incluye lo que ya existe; texto del `choca` por `NPR` |
| R51–R53 | node | 285 entre 5 = 57; ensayo sin `ensayo_id`; un solo `confirmado: true`; `puedeVolcar` en sus cuatro bordes; no se reintenta (`fetch` doble); avisos; relectura |
| R54, R55, R59 | node, pytest | Un texto por código; desconocido tal cual; sin identidad en `console` ni almacenamiento; una guarda de salida; aviso de PTE solo con `creado` |
| **R63** | node | `0002`, `0003` y un código que no está en `catalogo.listados` (tal cual); `TEXTO_TIPO` ya no existe |
| **R64** | node | Un tipo: el texto de la confirmación no cambia; dos tipos: su recuento con etiqueta |
| **R65, R66** | node | El texto de `tipo_no_valido` y el de `tipo_fuera_de_sigrid`; diez motivos en su orden; `tipo_no_valido` no suma a N |
| **R67** | node, pytest | `opcionesDeListado` con el actual vigente y con uno de baja; ninguna `option value=""` en el campo; el historial sin «sin listado» |
| **R68** | pytest | Las migas de `bandeja.html`: un enlace a `index.html` y la actual como `span aria-current="page"` (guarda R71 de F-035) |
| R57, R58 | raíz, pytest | Guardias de F-035 con F-040 `done`; catálogos mudados; documentos sin F-040 en futuro |
| **R69** | MANUAL | `tasks.md` T5.3–T5.6; la guardia de rutas de `test_f040_front.py` sigue negando cualquier otra |

## 8 · Riesgos y alternativas descartadas

1. **Descartadas**: `volcado.html` propia (D-2); reintento automático; trozos en paralelo; `x-data` propio; ensayar
   sin sincronizar (C-4). **Obra grande**: 57 trozos, 3–10 min de ensayos y otro tanto de volcados (peor caso, 40 s
   por trozo); barra y guarda de salida; `N` es Q-8.
2. **El ensayo caduca** a mitad: no se manda (R53.1) o 409 `caducado`; se vuelve a registrar lo que queda.
3. **Arranque en frío** de `sigrid-api` (35 s; F-074 pendiente): 502 o corte, repetir es inocuo; antes de T5.4, un
   ensayo de calentamiento. **Un volcado sin respuesta sigue escribiendo**: en duda y relectura; `PVI-` no duplica.
4. **Sigrid cambia**: la guarda relee en cada ensayo; entre ensayo y volcado (≤ 30 min) no, riesgo aceptado (S-6 de
   F-065). **Ruta y guarda difieren** con una `PVI-` en otra unidad: lo para la pasarela (`referencia_en_conflicto`).
5. **[E-1118] Un tipo de baja** entre aprobar y volcar: `rechazado` `tipo_no_valido` en el ensayo, nada escrito; la
   persona cambia el tipo y vuelve a aprobar (R65). Hoy los 4 tipos están vigentes.
6. **[E-1118] La etiqueta del tipo** depende de `catalogo.listados` de la carga de la página: si `auxtrcp` cambió
   desde entonces, sale el código tal cual (R63), nunca un nombre inventado.
7. **[E-1118] La primera escritura real**: el clasificador de permisos del líder bloqueó el clic final de T5.3 el
   2026-11-02; los clics que escriben (T5.3, T5.4) y `27_ -Abrir`/`28_` son **del humano** (R69).

## 9 · Frontera

**¿Cruza la frontera del proyecto? Sí.** El panel es quien dispara la **escritura en el ERP de producción**
(partes 708 por `POST /api/sigrid/partes-reclamacion`, vía F-059) y la lectura de las reclamaciones (vía F-065);
no añade rutas, tablas, variables ni recursos: consume los de F-059, F-065 y F-072 tal como están desplegados.
Documento del ecosistema: `azure-apps/postventa_incidencias.md` (y su copia `docs/INTEGRACION.md`) deja de hablar
de F-040 en futuro (R58, `tasks.md` T6 bis), con el protocolo de `CLAUDE.md`: `git pull --rebase`, solo ese
documento, commit aparte, push del humano y, ante un conflicto, parar.

## 10 · Hecho y no se rehace

Bloque 1 (T1–T3, APPROVED tras C-B1-1/C-B1-2; V3 aceptado), T4 (publicado el 2026-11-02, `dev` `b9a66db`), T5.1
y T5.2 (0626, 2026-11-02), T6a (publicada el 2026-11-05, `ed935ad`; M4 y M5 aceptados): `progress/impl_F-040_hasta_2026-11-05.md`.

## 11 · Puesta al día del 2026-11-18 (resumen)

Cada cambio va marcado **[E-1118]** en su sitio (§0, §1, §1.1, §2, §3.1, §3.2, §3.4, §4–§8); lo anterior, en `4b1eb21`.

## 12 · Decisiones

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| D-1 · Literales de Q-11 (R65, R66, R67) | (a) los de R65–R67; (b) otros que dicte el humano | (a) | (a) · humano, 2026-11-19 |
| D-2 · Recuento por tipo en el resumen del ensayo y en la confirmación (R64) | (a) solo cuando hay más de un tipo entre los previstos; (b) siempre; (c) no, solo la columna | (a) | (a) · humano, 2026-11-19 |
| D-3 · La opción en blanco «Sin listado» del formulario (R67) | (a) quitarla (nunca llega nulo; `0002` es una opción más) y añadir la del tipo no vigente; (b) renombrarla «En blanco (entra como 0002)»; (c) dejarla | (a) | (a) · humano, 2026-11-19 |
| D-4 · El enlace «Volcar a Sigrid» de R57 en `#/bandeja` | (a) ninguno nuevo: la tarjeta «Revisar la bandeja» de F-038 y la 02 del inicio dicen también que se vuelca; (b) una tarjeta más «Volcar a Sigrid» a `bandeja.html` | (a) | (a) · humano, 2026-11-19 |
| D-5 · Orden al retomar | (a) Bloque 1 bis → review → publicar (T11) → T5.3–T5.6 → T6; (b) T5.3–T5.6 con el front de hoy y el Bloque 1 bis después | (a): la primera escritura real se ve con el panel definitivo | (a) · humano, 2026-11-19 |
| D-6 · El tipo de la única escritura real de T5.4 (0626) | (a) la fila de prueba editada a `0003` POST VENTA y reaprobada, para ver en Sigrid (foto `28_`) que el parte nace con ese tipo; (b) tal cual (`0002`, tipo nulo heredado) | (a): cierra en producción R28 de F-072 con la misma escritura | (a) · humano, 2026-11-19 |
| D-7 · T5 bis paso 1 (un `choca` ensayado **sin** casilla → `conflicto_sin_confirmar`): desde el panel no se puede, «Ensayar» queda deshabilitado (T5.2, 2026-11-02) | (a) por la API del front con la sesión del humano, solo ensayo (como T26 de F-072); (b) quitar el paso: lo cubren los tests de F-065 | (a) | (a) · humano, 2026-11-19 |
| D-8 · Informes por encima de la puerta TAMAÑO (`impl_F-040.md` 520/220, `review_F-040.md` 457/140): `init.sh` en rojo en esta rama mientras F-040 no esté `done` | (a) `git mv` a `progress/impl_F-040_hasta_2026-11-05.md` y `progress/review_F-040_bloque1.md`, y unos nuevos que enlacen; (b) otra salida que diga el humano | (a) | (a) · humano, 2026-11-19 |
