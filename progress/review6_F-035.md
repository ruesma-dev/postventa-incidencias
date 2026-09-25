<!-- progress/review6_F-035.md -->
# F-035 · Review 6 · Correcciones de la review 5

> Revisado el **2026-09-25** sobre `feature/F-035-portal-posventa`, commit
> `e6a1afb`, rango `0ddaa56..e6a1afb` (commits `16daa43`, `3907c4e` y
> `e6a1afb`). Referencias: `progress/review5_F-035.md` y el apartado
> «Correcciones de la review 5» de `progress/impl_F-035.md`.
>
> **En esta revisión no he implementado ni corregido nada.** Las mutaciones
> se hicieron en un worktree desechable del scratchpad:
>
> - `git worktree add -b feature/F-035-rev6-tmp` sobre `e6a1afb`, con el
>   prefijo de rama para que corran los tests de rama;
> - el script (`mutar6.py`, en el scratchpad) escribe y restaura en bytes y
>   comprueba tras cada mutante que el fichero es idéntico al original;
> - al terminar, `git status --porcelain` del worktree estaba vacío, y se
>   hicieron `git worktree remove` y `git branch -D`.
>
> El árbol real sigue limpio. El único fichero que escribo en él es este, y
> no lo commiteo.

## Veredicto

**APPROVED** (APROBADO), **con observaciones**. F-035 **no se cierra** todavía:
falta T12 (V1 y V2 del humano).

**Lo que pedía la review 5 está hecho y lo he comprobado ejecutándolo:**

- `git diff 0ddaa56 e6a1afb` toca cinco ficheros: `progress/current.md`,
  `progress/impl_F-035.md`, `tests/test_f035_portal.py`,
  `tests_js/portal.test.js` y **una sola línea de producción**,
  `index.html:940`. Esa línea añade
  `:class="c.coste === null ? 'rs-sin-dato' : ''"` al coste del capítulo, la
  misma ligadura que la venta (941) y la diferencia (942). Es del portal
  (sección `economico`), no del circuito: `partes.html`, `css/*.css` y
  `js/*.js` no cambian.
- El vaciado del test de JS ya no tiene excepción:
  `ambitosDe(c, e, true)` en `tests_js/portal.test.js:1210`.
- **M17, M14 y M21 dan rojo** (tabla de §3).
- `bash harness/init.sh` está en verde.

**La muestra propia deja 10 supervivientes, pero ninguno justifica rechazar
según el criterio del líder.** He usado 21 mutantes con operadores que ni la
review 5 ni el implementer habían usado. Mueren 11 y sobreviven 10. Ninguno
de los 10:

- muestra algo roto hoy: he leído las líneas y el código actual es correcto;
  el hueco solo se vería si alguien las rompiera;
- toca el circuito: todos están en `index.html` (el portal) o en
  `css/portal.css`;
- es un test que se desactiva a sí mismo, que era el defecto de la review 5.

Son otra familia: comportamiento de la maqueta que **ningún requisito
numerado fija**. En concreto: la aritmética de «Diferencia», los enlaces de
navegación a la ficha, qué panel enseña cada pestaña de la ficha, el estilo
de `.rs-sin-dato` y el `:key` de una lista. Quedan anotados en
«Observaciones» para la ficha que haga real cada sección.

## Nivel de rigor

`estandar`, declarado en `harness/features.json`. Exige tres cosas:

- fase RED en los requisitos centrales;
- cobertura de las líneas cambiadas;
- campaña de mutación, con los supervivientes documentados y analizados.

Este rango no cambia Python de producción: la cobertura sale en N/A con el
motivo impreso y la campaña da 0 mutantes. Lo compensan las mutaciones a mano
(D-9).

## Verificación ejecutada por el reviewer

### 1 · `bash harness/init.sh`, tal cual

Terminó en **ENTORNO LISTO**:

- raíz: **73 passed**;
- `api` y `front`: en verde (desde la caché);
- `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`;
- `ruff`: 61 avisos, la misma deuda de antes.

En el worktree limpio, sin caché, el front da **353 passed** (la línea BASE
de `mutar6.py`).

### 2 · El diff

`git diff --stat 0ddaa56 e6a1afb`:

| Fichero | Cambio |
|---|---|
| `progress/current.md` | +15 |
| `progress/impl_F-035.md` | +239 |
| `services/postventa-front/index.html` | 1 línea (la 940) |
| `services/postventa-front/tests/test_f035_portal.py` | +53 −21 (R57 y R29) |
| `services/postventa-front/tests_js/portal.test.js` | +4 −4 (el vaciado) |

He leído el código nuevo de los dos tests:

- **R29** (antes «R9», que era la R-3 de la review 5): elige los chips por el
  token de clase `rs-ficha`, exige exactamente `CHIPS_DE_FICHA = 10` y que
  cada uno lea `datos.<bloque>.ficha`. Después aplica la comprobación de panel
  de siempre.
- **R57** (Python): elige los chips por lo que enseñan (un `rs-chip` cuyo
  `x-text` lee un `<x>.estado`), exige `CHIPS_DE_ESTADO = 5` y tiene una
  excepción **nombrada**, el chip del datamart. Después exige que
  `:data-estado` sea el mismo campo que se lee. Es la auditoría propia del
  implementer y el mismo patrón que pedía la review 5.

Ninguno de los dos tiene `print`, `console.log` ni secretos, y la primera
línea con la ruta se mantiene.

### 3 · Las verificaciones pedidas: M17, M14 y M21

Suite pytest completa del front (con `-x`), que incluye el puente a
`node --test`. Para los mutantes que mueren por el puente, saqué el test de
JS concreto con `node --test --test-reporter=tap` sobre el mismo mutante.

| Mutante | Resultado | Lo mata |
|---|---|---|
| M17 · `index.html:681`, se borra `:class="inc.ubicacion ? '' : 'rs-sin-dato'"` | **rojo** | JS «f035 R22/R25: «sin dato» se marca rs-sin-dato, y solo eso (review 4)» |
| M14 · `index.html:845`, `x-text="'F-999'"` | **rojo** | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| M21 · `index.html:214`, `x-text="'F-999'"` | **rojo** | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |

Los cambios requeridos 1 y 2 de la review 5 quedan **cumplidos**. El 3 (el
informe con los operadores nuevos, antes y después) también: la tabla del §3
del informe tiene 92 filas con el resultado antes y después.

### 4 · Muestra propia con operadores nuevos

**Operadores ya usados**, que he evitado:

- por el implementer: vaciar `:class`, `:data-estado` fijo, negar el
  `x-show`, cruzar los chips del volcado, apuntar la ficha al bloque
  siguiente, borrar el atributo, literal, intercambiar hermanos;
- por la review 5: invertir la polaridad, cambiar el campo, cruzar el coste
  con la venta, cambiar un umbral, quitar el filtro, bloque lejano.

**Operadores nuevos de esta review:**

- aritmética;
- constante de la comparación;
- errata en el nombre de la clase;
- CSS (borrar una regla, quitar o mover un selector);
- fuente del `x-for`;
- `:key` duplicable;
- `aria-current` de otra pestaña;
- condición de la pestaña de la ficha;
- argumento del manejador `@click`;
- **añadir** un atributo;
- clase estática quitada;
- destino del enlace;
- `data-placeholder` distinto de su ficha visible;
- borrar el marcador que usa el test (`data-vacio`);
- `some` por `every`;
- recortar el `x-text`.

| Mut. | Cambio | Resultado | Lo mata |
|---|---|---|---|
| N1 | 942: `c.venta - c.coste` → `c.coste - c.venta` | **VERDE** | nadie (ver O-3) |
| N2 | 942: `c.venta - c.coste` → `c.venta + c.coste` | **VERDE** | nadie (ver O-3) |
| N3 | 940: `c.coste === null` → `c.coste === 0` (el capítulo 9903 tiene coste 0) | rojo | JS «R22/R25: «sin dato»… (review 4)» |
| N4 | 940: `'rs-sin-dato'` → `'rs-sin-datos'` | rojo | JS «R22/R25: «sin dato»… (review 4)» |
| N5 | `portal.css:702`: `.rs-sin-dato {` → `.rs-sin-datoX {` | **VERDE** | nadie (ver O-4) |
| N6 | `portal.css:726`: se quita el selector `[data-estado="SAT"]` | rojo | JS «R57: cada código de estado (conest, revisión y volcado) tiene su regla [data-estado]…» |
| N19 | control de N6 (el mismo efecto, escrito de otra forma) | rojo | el mismo |
| N20 | `portal.css:742`: `TER` → `TER-x`, y `CER` se añade al grupo de `TER` | rojo | el mismo |
| N7 | 616: `x-for="inc in datos.incidencias.filas"` (la lista ignora el filtro) | rojo | `test_f035_r58_…[incidencias]` |
| N8 | 883: `:key="inc.id"` → `:key="inc.estado"` | **VERDE** | nadie (ver O-5) |
| N9 | 61: el `aria-current` de «Incidencias» mira `'impresion'` | rojo | `test_f035_r51_cada_pestana_de_la_barra_marca_su_propia_seccion` |
| N10 | 811: el panel «Parte» de la ficha se ve con `pestanaFicha === 'economico'` | **VERDE** | nadie (ver O-6) |
| N11 | 945: `@click="abrirCapitulo(c.nombre)"` | rojo | JS «R38/§5.8: la fila abierta, y solo ella, lleva rs-fila--abierta (review 4)» |
| N12 | 1006: se **añade** `:data-estado="f.estado"` al chip neutro del datamart | **VERDE** | nadie (ver O-7) |
| N13 | 630: `class="rs-chip"` → `class="rs-estado"` | rojo | JS «R57: todo elemento de index.html con data-estado es un rs-chip con su texto» |
| N14 | 968: el enlace del subpanel de capítulo va a `hashDe('impresion', …)` | **VERDE** | nadie (ver O-6) |
| N14b | 623: el enlace de la lista de incidencias va a `hashDe('impresion', …)` | **VERDE** | nadie (ver O-6) |
| N15 | un `data-placeholder="F-044"` → `"F-045"` (su ficha visible sigue en F-044) | rojo | JS «R9: cada data-placeholder de index.html lleva la ficha de su entrada en Portal.PLACEHOLDERS» |
| N16 | 893: se borra `data-vacio` (el marcador con el que R58 elige el vacío) | rojo | `test_f035_r58_…[impresion]` |
| N17 | 856: `.some(...)` → `.every(...)` en el vacío del historial | **VERDE** | nadie (ver O-6) |
| N18 | 939: `x-text="c.obra + ' · ' + c.nombre"` → `x-text="c.nombre"` | **VERDE** | nadie (ver O-3) |

Controles:

- **Base**: sin mutar, 353 passed.
- **Árbol**: cada mutante se restaura y se compara en bytes, y al final
  `git status --porcelain` da `''`.
- **N5, N6 y N14** no se aplicaron en la primera pasada (los finales de línea
  son CRLF y N14 tenía dos coincidencias). Los reescribí y los ejecuté aparte.
  Sus resultados son los de la tabla.

**Lectura.**

- **N16 importa.** Borrar el marcador que usa R58 para elegir **no** apaga el
  test: el test exige que el vacío exista. Es lo contrario del defecto de la
  review 5, y confirma la auditoría del §1 del informe del implementer.
- **N3 y N4 importan.** La línea nueva, la 940, queda protegida también
  contra operadores que no están en el barrido del implementer.

### 5 · Campaña del arnés

- **Alcance.** `harness.alcance.alcance_de_feature('F-035')` da
  `lineas = {}`, con origen `rama` y `54c0884..feature/F-035-portal-posventa`.
  La línea 940 es HTML, no Python.
- **Informe.** `progress/mutacion_F-035.md` declara 0 mutantes y
  «Tiempo total 0.0 s».
- **Reejecución.** Son menos de 5 minutos, así que reejecuté la campaña
  entera: `python -m harness.mutacion --feature F-035 --salida
  <scratchpad>/mutacion_rev6.md`. Da 0 mutantes, 0 muertos, 0 supervivientes
  y 0 timeouts, los mismos totales. Después `git status` quedó limpio.
- **Control del cero.** Lo hizo la review 3: 477 mutantes, todos en tests.
  Este rango solo añade una línea HTML, así que el cero sigue siendo por
  diseño.

## Checkpoints

**C1**

- [x] `bash harness/init.sh` termina con exit 0 (ENTORNO LISTO).
- [x] Existen los ficheros del arnés.

**C2**

- [x] Una sola feature `in_progress` (F-035).
- [x] La rama es `feature/F-035-portal-posventa`.
- [x] `current.md` tiene la entrada de estas correcciones y remite al informe.
  Sigue acumulando bloques anteriores: es la deuda O-2 de la review 1, no
  bloquea.
- [x] `history.md` no cambia en el rango. Ninguna feature pasa a `done`.

**C3**

- [x] Hexagonal: **N/A**, porque solo cambian tests y una línea del front
  estático, que no tiene capas.
- [x] La primera línea con la ruta sigue en los ficheros tocados.
- [x] Sin `print` ni `console.log` de depuración, sin TODO y sin secretos.
- [x] Sin dependencias nuevas.
- [x] Checkpoints de dominio (parte, firma, `conest`…): **N/A**. La única
  línea de producción es un `:class` de presentación de la maqueta. El
  circuito (`partes.html`, `js/*.js`) no cambia.
- [x] Ningún PDF ni parte escaneado en git.

**C3 bis**

- [x] **N/A**: el rango no toca `docs/referencia/`.

**C4**

- [x] **Cada requisito tiene un test trazable que lo verifica.** Los huecos
  de la review 5 (R22/R25 en la 681, y R29) están cerrados (§3). Los 10
  supervivientes del §4 caen en comportamiento que **ningún requisito
  numerado fija**:
  - R22 exige el **texto** «sin enlazar», y eso sí está probado; no exige el
    estilo de `.rs-sin-dato`;
  - no hay un R que defina la aritmética de «Diferencia», ni la navegación
    lista→ficha, ni qué panel enseña cada pestaña de la ficha.

  Van como observaciones, no como huecos de trazabilidad.
- [x] Los tests unitarios no tocan red ni BBDD.
- [x] Las verificaciones MANUAL tienen su guion (bloque 5b §9). **T12, con V1
  y V2 del humano, sigue pendiente**. No es un fallo del implementer.

**C4 bis**

- [x] `rigor: estandar` declarado.
- [x] **Fase RED: N/A justificado.** Los tests enmendados cierran huecos de
  prueba sobre un comportamiento que ya era correcto. La línea 940 es la
  excepción: su «rojo» es la traza del informe (§2, «940 sin :class»), y la
  he reproducido con N3 y N4.
- [x] **Cobertura: N/A**, con el motivo impreso por `init.sh`.
- [x] **Mutación**: 0 mutantes, comprobados con el alcance recalculado y con
  la reejecución.
- [x] **Muertos comprobados**: se declaran 0.0 s, así que reejecuté la
  campaña. Mismos totales y árbol limpio.
- [x] **Coste por mutante: N/A**, porque no hay ningún mutante de campaña.
- [x] **Supervivientes analizados.**
  - Los de la campaña: ninguno.
  - Los del barrido a mano del implementer: 0, y lo confirmo con M17, M14 y
    M21.
  - Los 10 de mi muestra: analizados uno a uno en «Observaciones». No son
    equivalentes, pero cumplen el criterio de proporcionalidad del líder: no
    rompen nada visible hoy, no tocan el circuito y no hay un requisito
    numerado que los cubra.
- [x] Las «Evidencias» de esta vuelta traen los cuatro números.
- [x] Ningún N/A va sin su motivo.
- [x] **Orden (punto 7): N/A.** El rigor es `estandar`, no `critico`, y
  ningún requisito de esta vuelta protege un orden entre colaboradores.

**C4 ter**

- [x] **N/A**: `harness/rutas_sensibles.json` no existe.

**C5**

- [x] En `tasks.md`, T12 sigue `[ ]` por diseño (humano). Esta vuelta no
  abre tareas: los commits son la corrección de la review, con el mismo
  formato que en las vueltas anteriores.
- [x] No hay ficheros temporales ni sin trackear, y el árbol está limpio.
- [x] `features.json` dice `in_progress`, que es el estado real.

## Cobertura: requisito → test (lo que cambia en esta vuelta)

| R | Test | Estado |
|---|---|---|
| R22 / R25 («sin dato») | JS `f035 R22/R25: «sin dato» se marca rs-sin-dato, y solo eso (review 4)`, con el vaciado sin excepción | verde; caza M17, N3, N4 y la 940 sin `:class` |
| R29 (chip de ficha de cada panel) | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` (antes «r9») | verde; caza M14, M21 y M13 |
| R57 (color del chip = estado leído) | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` (elige por lo que enseña) y los JS de R57 | verde; caza N6, N13, N19 y N20 |
| R58 (vacío en lugar de la tabla) | `test_f035_r58_…[×3]` | verde; caza N7 y N16 |
| R51 (pestaña actual) | `test_f035_r51_cada_pestana_de_la_barra_marca_su_propia_seccion` | verde; caza N9 |
| R38 / §5.8 (fila abierta) | JS `R38/§5.8: la fila abierta…` | verde; caza N11 |
| R9 (placeholders) | JS `R9: cada data-placeholder de index.html lleva la ficha de su entrada…` | verde; caza N15 |

El resto de R1–R61 no cambia desde la review 5.

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean; para las fichas que conviertan cada sección en real)

- **O-1 · T12.** V1 y V2 del humano, con el guion en el bloque 5b §9, siguen
  pendientes. F-035 no puede pasar a `done` hasta que el humano las haga y
  las anote en `current.md`. En V1 conviene mirar además la 940 con un
  capítulo sin coste (los datos de ejemplo no tienen ninguno).
- **O-2 · `current.md`.** La deuda O-2 de la review 1 sigue abierta.
- **O-3 · Tabla de capítulos (`index.html:939` y `942`): para F-046 y F-047.**
  Ningún test fija la fórmula de «Diferencia»: N1 y N2 sobreviven con el
  signo invertido o con una suma. Tampoco fija que la celda del capítulo lleve
  el código de la obra (N18). Hoy es correcto (`c.venta - c.coste`). Cuando
  F-047 la haga real, la fórmula necesita un requisito y un test que compruebe
  el valor. Los datos de ejemplo ya traen el caso que haría falta: el
  capítulo 9901, con coste 1250 y venta 1500. Hoy muestra 250 € y, con N1,
  mostraría −250 € sin que falle ningún test.
- **O-4 · Estilo de «sin dato» (`css/portal.css:702`).** Si se borra la regla
  `.rs-sin-dato`, ningún test lo nota (N5). La clase se pone bien, pero no se
  comprueba que la hoja la pinte. Es un hueco de la misma familia que R57, que
  sí exige su regla `[data-estado]` en la hoja. Basta con una aserción al
  estilo de «cada código de estado tiene su regla».
- **O-5 · `:key` de las listas (N8).** Una clave repetible (`inc.estado`) no
  la caza nadie. Con claves repetidas, Alpine puede reutilizar mal los nodos
  al filtrar. Es de gravedad baja en la maqueta, y conviene fijarlo cuando las
  listas lean datos reales.
- **O-6 · Navegación dentro de la maqueta: para F-036 y F-044.**
  - N14 y N14b: los enlaces a la ficha (lista de incidencias, 623; subpanel
    de capítulo, 968) pueden apuntar a otra sección sin que falle nada.
  - N10: la condición del panel «Parte» de la ficha puede cambiarse de
    pestaña.
  - N17: el vacío del historial puede pasar de `some` a `every`.

  Los tests actuales comprueban la función (`hashDe`, `verPestanaFicha`,
  etc.) pero no la ligadura del HTML con cada sección. Es el mismo patrón
  que R58 cerró para las listas.
- **O-7 · El chip neutro del datamart (N12).** La excepción nombrada del test
  R57 de Python lo saca del recorrido. Por eso, **añadirle** un
  `:data-estado` pasa sin que nada falle, y solo le pondría el punto de color
  de `.rs-chip[data-estado]::before`. Si F-048 conserva ese chip neutro,
  conviene exigir que **no** lleve `data-estado`.
- **R-2 de la review 4** (`display: NONE` y `visibility: collapse` en la
  guardia de R-1) sigue abierta.

## Automejora (propuesta, no aplicada)

**P-R5** · para `.claude/agents/reviewer.md` §«Validación contra el nivel de
rigor», y de ahí a `arnes-base`.

Cada vuelta de review ha pedido «operadores que nadie haya usado todavía».
Es útil, pero **no converge por sí solo**: siempre hay otro operador (en esta
vuelta, la aritmética, el CSS o la navegación) que encuentra algo fuera de lo
que la spec fija.

Propongo escribir en el protocolo el criterio de proporcionalidad que ha dado
el líder en esta vuelta:

- En una feature de rigor `estandar` cuyo alcance sea una **maqueta** o
  presentación sin datos reales, un superviviente de la muestra propia del
  reviewer **bloquea** solo en dos casos:
  - (a) cae en un requisito numerado de la spec;
  - (b) o afecta a algo que ya se ve roto, o al circuito en producción.
- El resto va a «Observaciones», **asignado a la ficha** que hará real esa
  parte. Así se arrastra con dueño y no reabre la feature.
- El reviewer declara en su informe **qué operadores ha usado**, para que la
  vuelta siguiente no los repita.

Caso de origen: F-035, reviews 4 a 6.
