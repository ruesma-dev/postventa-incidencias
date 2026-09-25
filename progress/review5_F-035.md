<!-- progress/review5_F-035.md -->
# F-035 · Review 5 · Correcciones de la review 4

> Revisado el **2026-09-25** sobre `feature/F-035-portal-posventa`, commit
> `e5f85a8`, rango `effbafa..e5f85a8`. Referencias:
> `progress/review4_F-035.md` y el apartado «Correcciones de la review 4» de
> `progress/impl_F-035.md`.
>
> **En esta revisión no he implementado ni corregido nada.** Todas las
> mutaciones se hicieron en un worktree desechable del scratchpad:
>
> - se creó con `git worktree add -b feature/F-035-rev5-tmp` sobre `e5f85a8`,
>   con el prefijo de rama para que corran los tests de rama;
> - el script (`mutar5.py`, en el scratchpad) escribe y restaura en bytes, y
>   comprueba al final que `index.html` es idéntico al original;
> - al final `git status` del worktree estaba vacío, y se hicieron
>   `git worktree remove` y `git branch -D`.
>
> El árbol real sigue limpio. El único fichero que escribo en él es este, y
> no lo commiteo.

## Veredicto

**CHANGES_REQUESTED** (RECHAZADO).

**Lo que pedía la review 4 está hecho y lo he comprobado ejecutándolo:**

- las tres negaciones de la lista (298, 599 y 882) dan **rojo**, cada una en
  su parámetro de R58;
- la fila P-R1 está corregida;
- el diff solo toca tests, el informe y `current.md`;
- `init.sh` está en verde;
- el hallazgo de §4 (`index.html:940`) está bien descrito, y lo he
  reproducido.

**Por qué rechazo.** He tomado una muestra propia de 24 mutantes con
operadores **distintos** de los del implementer. Mueren 21 y sobreviven 3,
que no son equivalentes. Los tres salen de un mismo defecto de diseño en dos
de los tests nuevos: **el test elige qué comprobar según la misma ligadura que
se está mutando**. Si la ligadura se borra, o cambia de forma, el elemento
deja de estar en lo que el test mira, y la suite sigue en verde.

- **M17 · Quitar el `:class` de `index.html:681`**, la ubicación en la ficha
  de la incidencia, da **verde**. Es justo la aparición que el informe
  (§3) dice haber cerrado con la «fila vaciada». El test de JS solo vacía la
  fila en los elementos que **tienen** `:class`
  (`tests_js/portal.test.js:1210`, `ambitosDe(c, e, ":class" in e.atributos)`).
  Si se borra el atributo, el vaciado se apaga para ese elemento. Ninguna
  incidencia de ejemplo carece de ubicación, así que la suite no ve nada.
  **No es equivalente**, y el propio informe da el argumento: «la ligadura
  existe para cuando falte el dato». Con una incidencia sin ubicación se leería
  «sin completar» sin `rs-sin-dato`, que es lo mismo que el informe describe
  como defecto en `index.html:940`.
- **M14 · Cambiar el chip de `index.html:845` a `x-text="'F-999'"`**, y
  **M21 · lo mismo en `index.html:214`**, dan **verde**. El test R9
  (`tests/test_f035_portal.py:2015-2020`) elige los chips por la **forma** de
  su `x-text` (`^datos\.(\w+)\.ficha$`). Un chip con un literal deja de ser
  chip para el test, y el umbral `len(chips) >= 7` (hay 10) deja escapar hasta
  tres. **No es equivalente**: el panel de vínculos diría «F-999» en lugar de
  «F-047». Si se renumera la ficha, un literal correcto también se quedaría
  desfasado.

Es el mismo tipo de hueco que la review 4 encontró en R58, donde el test
buscaba «que contenga la función» y no la forma. Aquí el test se desactiva a
sí mismo cuando desaparece el enganche. Se arregla en los dos tests, con
dos o tres líneas en cada uno (ver «Cambios requeridos»). No hay que tocar
producción.

**T12** (V1 y V2 del humano) sigue pendiente. No es un fallo del implementer,
pero F-035 no puede cerrarse sin ella.

## Nivel de rigor

`estandar`, declarado en `harness/features.json`. Exige tres cosas:

- fase RED en los requisitos centrales;
- cobertura de las líneas cambiadas;
- campaña de mutación, con los supervivientes documentados y analizados.

Este rango no cambia Python de producción, así que:

- la cobertura sale en N/A, con el motivo impreso;
- la campaña da 0 mutantes;
- lo que compensa son las mutaciones a mano (D-9).

## Verificación ejecutada por el reviewer

### 1 · `bash harness/init.sh`, tal cual

Terminó en **ENTORNO LISTO**:

- raíz: **73 passed**;
- `api` y `front`: en verde (desde la caché);
- `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`;
- `ruff`: 61 avisos, la misma deuda de antes.

En el worktree limpio, el front da **353 passed**, sin caché. `node --test
tests_js/*.test.js` da **413/413**. Coinciden con lo que declara el informe.

### 2 · El diff solo toca tests, informe y `current.md`

`git diff --stat effbafa e5f85a8` tiene exactamente cuatro entradas:

- `progress/current.md` (+15);
- `progress/impl_F-035.md` (+200 −2);
- `services/postventa-front/tests/test_f035_portal.py` (+48);
- `services/postventa-front/tests_js/portal.test.js` (+195).

No hay nada de `partes.html`, `index.html`, `css/*.css` ni `js/*.js`. Los
commits son `e03b173`, `1c79ed1` y `e5f85a8`. He leído entero el código nuevo
de los dos ficheros de test:

- no hay `print` ni `console.log`;
- no hay secretos;
- los tests de JS usan el componente real sin red (`conVentanaFalsa`,
  `nuevoComponente`);
- `ruff` se queda en 61 avisos.

### 3 · Las tres negaciones de la lista

Pasé la suite pytest completa del front (con `-x`), que incluye el puente a
`node --test`:

| Mutante | Resultado | Lo mata |
|---|---|---|
| `index.html:298` → `x-show="!bandejaFiltrada().length"` | **rojo** | `test_f035_r58_…[bandeja]` |
| `index.html:599` → `x-show="!incidenciasFiltradas().length"` | **rojo** | `test_f035_r58_…[incidencias]` |
| `index.html:882` → `x-show="!impresionFiltrada().length"` | **rojo** | `test_f035_r58_…[impresion]` |

El cambio 1 de la review 4 queda **cumplido**.

### 4 · Muestra propia del barrido, distinta de la del implementer

El implementer usó cinco operadores:

- `:class` → `''`;
- `:data-estado` → `'SAT'`;
- negar el `x-show`;
- cruzar los chips del volcado;
- apuntar la ficha al bloque siguiente.

Yo he usado otros:

- invertir la polaridad;
- cambiar el campo;
- cruzar el coste con la venta;
- cambiar un umbral;
- quitar el filtro;
- apuntar la ficha a un bloque lejano;
- poner un literal;
- **borrar el atributo entero**.

Para los que mueren en el puente de JS, el test que los mata lo saqué con
`node --test --test-reporter=spec tests_js/portal.test.js` sobre el mismo
mutante.

| Mut. | Cambio | Resultado | Lo mata |
|---|---|---|---|
| M1 | 317: `filaBandejaAbierta !== fila.id` | **rojo** | JS «R38/§5.8: la fila abierta, y solo ella…» |
| M2 | 374: `:class` invertida (`? 'rs-sin-dato' : ''`) | **rojo** | JS «R22/R25: «sin dato»…» |
| M3 | 1037: `:class="'rs-toast--visible'"` (siempre) | **rojo** | JS «R11: el aviso de un placeholder…» |
| M4 | 740: `c.nota ? 'rs-nota--atencion'` (otro campo) | **rojo** | JS «R25: un pendiente del campo…» |
| M5 | 941: `c.coste === null ?` (otro campo) | **rojo** | JS «R22/R25: «sin dato»…» |
| M6 | 836: `:class` con `importe(v.coste)` (cruzado) | **rojo** | JS «R22/R25: «sin dato»…» |
| M7 | 937: `capituloAbierto ?` (sin comparar) | **rojo** | JS «R38/§5.8…» |
| M8 | 229: `errores.length > 1` | **rojo** | `test_f035_entrada_la_lista_de_errores_…` |
| M9 | 489: `r.resultado !== datos.volcado.dryRun` | **rojo** | `test_f035_r40_cada_chip_del_volcado_va_en_su_panel` |
| M10 | 889: `:data-estado="inc.id"` | **rojo** | `test_f035_r57_el_color_de_cada_chip_…` |
| M11 | 298: `x-show="datos.bandeja.filas.length"` (sin filtro) | **rojo** | `test_f035_r58_…[bandeja]` |
| M12 | 893: `x-show="!incidenciasFiltradas().length"` (otro filtro) | **rojo** | `test_f035_r58_…[impresion]` |
| M13 | 179: `datos.capitulos.ficha` (bloque lejano) | **rojo** | `test_f035_r9_el_chip_de_cada_panel_…` |
| **M14** | 845: `x-text="'F-999'"` | **VERDE** | nadie (el test R9 deja de ver ese chip) |
| M16 | 972: `:class` con `.venta` en lugar de `.coste` | **rojo** | JS «R22/R25: «sin dato»…» |
| **M17** | 681: **se borra** `:class="inc.ubicacion ? '' : 'rs-sin-dato'"` | **VERDE** | nadie (sin `:class`, el test no vacía la fila) |
| M18 | 834: se borra el `:class` | **rojo** | JS «R22/R25: «sin dato»…» (EJ-0002 no tiene proforma) |
| M19 | 374: se borra el `:class` | **rojo** | JS «R22/R25: «sin dato»…» |
| M20 | 630: se borra `:data-estado` | **rojo** | JS «R57: ningún estado se pinta fuera de su chip…» |
| **M21** | 214: `x-text="'F-999'"` | **VERDE** | nadie (el mismo motivo que M14) |
| M22 | 942: se borra el `:class` | **rojo** | JS «R22/R25: «sin dato»…» (el capítulo 9902 tiene venta `null`) |

Tres controles más:

- **Base**: sin mutar, 353 passed.
- **Mutante del propio informe**: la 681 con `:class="''"` da **rojo**. Lo mata
  JS «R22/R25». La tabla del implementer es cierta con sus operadores.
- **Árbol**: tras cada mutante, `index.html` se restaura y se compara en
  bytes.

**Cómo se lee M18, M19 y M22 frente a M17.** Borrar el `:class` solo lo caza
el test cuando los datos de ejemplo ya traen el hueco en ese sitio. En la 681
no lo traen, y el vaciado que debía cubrirlo depende de que exista el
atributo borrado. La protección de la 681 que el informe da por hecha solo vale
contra el operador `''`.

### 5 · El «hueco latente» de §4 está bien descrito

Lo reproduje en la copia desechable. Cambié la línea 1210 del test de JS a
`ambitosDe(c, e, true)`, es decir, apliqué el vaciado a todos los candidatos:

```
✖ f035 R22/R25: «sin dato» se marca rs-sin-dato, y solo eso (review 4)
  AssertionError [ERR_ASSERTION]: la marca rs-sin-dato no cuenta lo mismo que el texto
  +   '<td x-text="importe(c.coste)"> dice «sin enlazar» sin rs-sin-dato'
```

Sale **un único** problema, y es exactamente el que describe el informe:
`index.html:940`, el coste del capítulo, no lleva `rs-sin-dato`, mientras que
la 941 y la 942 sí. Hoy es latente: los tres capítulos de ejemplo tienen
coste (1250, 980 y 0). Está bien que no lo arreglara, porque el encargo
prohibía tocar `index.html`.

Lo que **no** está bien es cómo lo aparta del test. Filtra por
«tiene `:class`», y eso abre M17. Ver el cambio requerido 1.

### 6 · Campaña del arnés

- **Alcance.** `harness.alcance.alcance_de_feature('F-035')` da
  `lineas = {}`, con origen `rama` y `54c0884..feature/F-035-portal-posventa`.
- **Informe.** `progress/mutacion_F-035.md` declara 0 mutantes y
  «Tiempo total 0.0 s».
- **Reejecución.** Como son menos de 5 minutos, reejecuté la campaña entera:
  `python -m harness.mutacion --feature F-035 --salida <scratchpad>/mutacion_rev5.md`.
  Da 0 mutantes, 0 muertos, 0 supervivientes y 0 timeouts, los mismos
  totales. Después `git status` quedó limpio.
- **Control del cero.** Lo hizo la review 3: 477 mutantes, todos en tests.
  Este rango solo añade tests, así que el cero sigue siendo por diseño.

## Checkpoints

**C1**

- [x] `bash harness/init.sh` termina con exit 0.
- [x] Existen los ficheros del arnés.

**C2**

- [x] Una sola feature `in_progress` (F-035).
- [x] La rama es `feature/F-035-portal-posventa`.
- [x] `current.md` tiene la entrada de estas correcciones y remite al
  informe. Sigue acumulando bloques anteriores: es la deuda O-2 de la
  review 1, no bloquea.
- [x] `history.md` no cambia en el rango. Ninguna feature pasa a `done`.

**C3**

- [x] Hexagonal: **N/A**, porque solo cambian tests del front estático.
- [x] La primera línea con la ruta sigue en los dos ficheros de test y en los
  dos `.md`.
- [x] Sin `print` ni `console.log` de depuración, sin TODO y sin secretos.
- [x] Sin dependencias nuevas: los tests de JS usan `node:test` y
  `node:assert`, que ya se usaban.
- [x] Checkpoints de dominio (parte, firma, `conest`…): **N/A**. El rango no
  toca lógica del circuito, porque el diff no incluye ningún fichero de
  producción.
- [x] Ningún PDF ni parte escaneado en git.

**C3 bis**

- [x] **N/A**: el rango no toca `docs/referencia/`.

**C4**

- [ ] **Cada requisito tiene un test trazable que lo verifica.** R58 ya ve la
  polaridad de la lista (§3). Pero quedan dos huecos:
  - el «sin dato» de la ubicación de la incidencia (R22/R25, `index.html:681`)
    deja de verse si se borra su `:class` (M17);
  - el chip de ficha de cada panel deja de verse si su `x-text` no tiene la
    forma `datos.X.ficha` (M14 y M21).

  Son los cambios requeridos 1 y 2.
- [x] Los tests unitarios no tocan red ni BBDD. Los de JS instancian el
  componente con la red prohibida.
- [x] Las verificaciones MANUAL tienen su guion (bloque 5b §9). **T12, con
  V1 y V2 del humano, sigue pendiente** (`tasks.md:261`). No es un fallo del
  implementer.

**C4 bis**

- [x] `rigor: estandar` declarado.
- [x] **Fase RED: N/A justificado.** Los tests nuevos cierran huecos de
  prueba sobre un comportamiento que ya era correcto. Sin una mutación
  delante no hay rojo posible. Su «rojo» son las trazas de mutación del
  informe, y he reproducido las tres del cambio 1 (§3) y la 681 (§4).
- [x] **Cobertura: N/A**, con el motivo impreso por `init.sh`.
- [x] **Mutación**: 0 mutantes, comprobados con el alcance recalculado y
  con la reejecución.
- [x] **Muertos comprobados**: 0.0 s declarados, así que reejecuté la
  campaña. Mismos totales y árbol limpio.
- [x] **Coste por mutante: N/A**, porque no hay ningún mutante.
- [ ] **Supervivientes analizados.** Los de la campaña: ninguno. En las
  mutaciones a mano que compensan (D-9), M14, M17 y M21 **sobreviven, no
  son equivalentes y no están documentados**. El informe da «0 supervivientes»
  y da la 681 por cerrada. Eso es cierto con sus operadores, pero no
  contra el borrado del atributo. Son los cambios requeridos 1 y 2.
- [x] Las «Evidencias» de esta vuelta traen los cuatro números.
- [x] Ningún N/A va sin su motivo.

**C4 ter**

- [x] **N/A**: `harness/rutas_sensibles.json` no existe.

**C5**

- [x] En `tasks.md`, T14–T19 siguen `[x]` y T12 `[ ]`, por diseño (humano).
  Esta vuelta no abre tareas: los commits `e03b173` y `1c79ed1` son la
  corrección de la review, con el mismo formato que en las vueltas
  anteriores.
- [x] No hay ficheros temporales ni sin trackear, y el árbol está limpio.
- [x] `features.json` dice `in_progress`, que es el estado real.

## Cobertura: requisito → test (lo que cambia en esta vuelta)

| R | Test | Estado |
|---|---|---|
| R58 | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[×3]` (enmendado) | verde; caza 298, 599 y 882 negadas, M11 y M12 |
| R9 / R24 (chip de ficha de cada panel) | `test_f035_r9_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` | verde; caza el cruce de bloque (M13 y las 10 del barrido), **no** el literal (M14 y M21) |
| R22 / R25 («sin dato») | JS `f035 R22/R25: «sin dato» se marca rs-sin-dato, y solo eso (review 4)` | verde; caza M2, M5, M6, M16, M18, M19 y M22, **no** M17 |
| R25 (pendiente del campo) | JS `f035 R25: un pendiente del campo se pinta en atención, y solo él (review 4)` | verde; caza M4 |
| R38 / §5.8 (fila abierta) | JS `f035 R38/§5.8: la fila abierta, y solo ella, lleva rs-fila--abierta (review 4)` | verde; caza M1 y M7 |
| R11 (tarjeta del aviso) | JS `f035 R11: el aviso de un placeholder se ve en su tarjeta, y sin aviso no hay tarjeta (review 4)` | verde; caza M3 |

El resto de R48–R61 no cambia desde la review 4: sigue en verde con los
mismos tests (M8, M9, M10 y M20 lo confirman).

## Cambios requeridos

1. **El vaciado del «sin dato» no puede depender del atributo que protege.**
   El sitio es `services/postventa-front/tests_js/portal.test.js:1210`:

   ```js
   for (const ambito of ambitosDe(c, e, ":class" in e.atributos)) {
   ```

   Hay que vaciar la fila en **todos** los candidatos, salvo una excepción
   **nombrada**: el único elemento del hallazgo §4, el
   `<td x-text="importe(c.coste)">` de `index.html:940`. Por ejemplo, una
   constante con esa expresión, comentada y con remisión al hallazgo, en
   lugar de «tiene `:class`». Conviene además que el test **falle si la
   excepción deja de hacer falta**, para que se retire cuando se arregle la
   940.

   Si el líder decide arreglar ya `index.html:940`, basta con quitar el
   filtro y la excepción sobra. Pero eso toca producción, y lo decide él.

   **Verificación**: en una copia desechable, borrar entero
   ` :class="inc.ubicacion ? '' : 'rs-sin-dato'"` de `index.html:681` tiene
   que dar **rojo**. Pega la traza. La 681 con `:class="''"` tiene que seguir
   en rojo.

2. **El test R9 elige los chips por su clase, no por la forma de su ligadura.**
   El sitio es `services/postventa-front/tests/test_f035_portal.py:2015-2020`
   (`test_f035_r9_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes`).
   Hay que tomar todos los elementos con la clase `rs-ficha` (hoy son
   exactamente los 10 chips; `rs-ficha-cabecera` es otra clase y no cuenta).
   Después, exigir que **cada uno** tenga un `x-text` de la forma
   `datos.<bloque>.ficha`, y sobre eso aplicar la comprobación de panel que
   ya existe. El umbral `>= 7` sobra, o pasa a exigir los 10.

   **Verificación**: en una copia desechable, `x-text="'F-999'"` en
   `index.html:845` y en `index.html:214` tienen que dar **rojo**. Pega las
   trazas. Las 10 del barrido del implementer (bloque siguiente) y M13
   (bloque lejano) tienen que seguir en rojo.

3. **Informe.** Añade estos operadores al apartado del barrido de
   `progress/impl_F-035.md`: borrar el atributo, y un literal en el chip. Pon
   su resultado antes y después de los cambios 1 y 2.

Solo toca los tests y el informe. Ni `partes.html`, ni `index.html`, ni
`css/*.css`, ni `js/*.js`. Después, `bash harness/init.sh` tiene que seguir
en verde.

## Recomendaciones (no bloquean)

- **R-2 de la review 4** sigue abierta: `display: NONE` y
  `visibility: collapse` en la guardia de R-1. Puede ir en el mismo encargo.
- **R-3 · El nombre del test R9.** R9 habla de los **placeholders**
  (`data-placeholder`), no de los chips de los paneles. Lo que protege
  `test_f035_r9_el_chip_de_cada_panel_…` se parece más a R24 (cada bloque de
  datos de ejemplo declara la ficha que lo sustituirá) y a R29. Conviene
  renombrarlo o citar el requisito correcto en su comentario, por
  trazabilidad.

## Observaciones

- **O-1**: T12 (V1 y V2 del humano, guion en el bloque 5b §9) sigue
  pendiente. F-035 no se puede cerrar hasta que el humano la haga y la anote
  en `current.md`. No cuenta como fallo del implementer.
- **O-2**: el hallazgo de §4 (`index.html:940`) queda para el líder. Es una
  línea de la maqueta, no del circuito.

## Automejora (propuesta, no aplicada)

**P-R4** · para `.claude/agents/reviewer.md` §«Validación contra el nivel de
rigor» y para `CHECKPOINTS.md` C4 bis, y de ahí a `arnes-base`. Complementa
P-R3.

- **En las mutaciones a mano, el operador «borrar el atributo» es
  obligatorio**, además de «vaciarlo» o «negarlo».
- **Y el reviewer mira cómo elige el test qué comprobar.** Si un test
  selecciona los elementos por la misma ligadura que protege, ya sea porque
  «tiene `:class`» o porque «su `x-text` casa con `datos.X.ficha`», borrar o
  cambiar la forma de esa ligadura saca al elemento del test, y la suite sigue
  en verde. La selección tiene que ir por algo que la mutación no toque: la
  clase fija, el rol, el texto del dato.

Caso de origen: F-035, review 5, con M17 (`index.html:681` sin `:class`) y
M14 y M21 (chips con literal).
