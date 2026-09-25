<!-- progress/review4_F-035.md -->
# F-035 · Review 4 · Correcciones de la review 3

> Revisado el **2026-09-25** sobre `feature/F-035-portal-posventa`, commit
> `1ab3504`, rango `75e2ec0..1ab3504`. Referencias:
> `progress/review3_F-035.md` y el apartado «Correcciones de la review 3» de
> `progress/impl_F-035.md`.
>
> **En esta revisión no he implementado ni corregido nada.** Todas las
> mutaciones se hicieron en un worktree desechable del scratchpad:
>
> - se creó con `git worktree add -b feature/F-035-rev4-tmp`, con el prefijo
>   de rama para que corran los tests de rama;
> - cada mutante se restauró al terminar;
> - al final `git status` del worktree estaba vacío, y se hicieron
>   `git worktree remove` y `git branch -D`.
>
> El árbol real sigue limpio. El único fichero que escribo en él es este, y
> no lo commiteo.

## Veredicto

**CHANGES_REQUESTED** (RECHAZADO).

**Lo que pedía la review 3 está hecho y lo he comprobado ejecutándolo:**

- G (en las dos hojas), S1, O2, H, I y R dan **rojo**.
- O también da rojo. Es equivalente en comportamiento, y el implementer lo
  fija a propósito.
- El diff solo toca tests, el informe y `current.md`.
- `init.sh` está en verde.
- La categoría P-R1 tiene las 37 directivas, contadas igual que yo.

**Por qué rechazo.** Al barrer una mutación por **cada aparición** de las 37
directivas, en lugar de una por clase, aparece un hueco nuevo. En la clase
«`x-show` de estado vacío y de lista», que el informe da como «**Muertas**»,
los tres `x-show` de **lista** se pueden negar con la suite en verde:

- `index.html:298` (bandeja);
- `index.html:599` (incidencias);
- `index.html:882` (impresión).

No son equivalentes. Lo he comprobado en Chrome: con filas, la sección se
queda **sin tabla y sin estado vacío**, en blanco. Eso rompe R58 («un estado
vacío **en lugar de** la tabla»), y el análisis no está documentado en
ninguna parte.

Es el mismo tipo de hueco que O2, que la review 3 exigió cubrir. Aquí no se
cubrió porque el test de R58 comprueba la polaridad del `x-show` del vacío,
pero **no** la del contenedor de la lista. Se arregla con una aserción (ver
«Cambios requeridos»).

Reconozco que la review 3 no lo vio: allí solo mutó el vacío (mutante M).
Lo encuentro ahora porque el barrido es por aparición y no por muestra.

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
- `api` y `front`: verdes (desde la caché);
- `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`;
- `ruff`: 61 avisos, la misma deuda de antes.

En el worktree limpio, el front da **352 passed**. Son los 346 de antes más
los 6 nuevos, e incluyen el puente con los 409 tests de JavaScript.

### 2 · El diff solo toca tests, informe y `current.md`

`git diff --stat 75e2ec0 1ab3504` tiene exactamente tres entradas:

- `progress/current.md` (+16);
- `progress/impl_F-035.md` (+198);
- `services/postventa-front/tests/test_f035_portal.py` (+148, solo altas).

No hay nada de `partes.html`, `index.html`, `css/*.css` ni `js/*.js`. He
leído entero el código de los 6 tests nuevos:

- no hay `print`;
- no hay secretos;
- son lecturas de ficheros;
- `ruff` se queda en 61 avisos.

### 3 · Mis mutantes de la review 3 y variantes, en la copia desechable

Script propio (`mutar4.py`, en el scratchpad). Cada mutante es una
sustitución con su número exacto de coincidencias, y los finales de línea se
conservan (lectura y escritura en bytes). Después pasa la suite pytest del
front completa, que incluye el puente a `node --test`.

| Mut. | Cambio | Resultado | Lo mata |
|---|---|---|---|
| base | ninguno | 352 passed | |
| **G** `styles.css` | las 3 apariciones de `:is(*, #rs-movimiento-reducido)` → `*` | **rojo** | `…r55_el_movimiento_reducido_gana_por_especificidad[styles.css]` |
| **G** `portal.css` | lo mismo en la otra hoja | **rojo** | `…[portal.css]` |
| G2 (mío) | `:is(*, #…)` → `:is(*, .rs-movimiento-reducido)` (especificidad de clase) | **rojo** | `…[styles.css]` |
| **S1** | «Simulación» con `…=== datos.volcado.hecho` | **rojo** | `…r40_cada_chip_del_volcado_va_en_su_panel` |
| S1b (mío) | «Hecho en Sigrid» con `…=== datos.volcado.dryRun` | **rojo** | el mismo |
| **O2** | `<ul x-show="!datos.entrada.errores.length"` | **rojo** | `…la_lista_de_errores_de_la_importacion_se_ve_cuando_hay_errores` |
| **O** | ese `x-show` a `"true"` | **rojo** | el mismo, porque fija la expresión (lo declara el informe, y estoy de acuerdo) |
| DE | `:data-estado="'SAT'"` en el primer `inc.estado` | **rojo** | `…r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` |
| **H** | `display: none` en `.rs-aviso--info` | **rojo** | `…r60_styles_css_no_puede_esconder_ni_desactivar_el_circuito` |
| **I** | `pointer-events: none` en `.rs-btn` | **rojo** | el mismo |
| **R** | `visibility: hidden` en `.rs-panel--destacado` | **rojo** | el mismo |
| H2 (mío) | `display: NONE` en `.rs-aviso--info` | verde | fuera del perímetro de R-1 (recomendación R-2) |
| R2 (mío) | `visibility: collapse` en `.rs-panel--destacado` | verde | fuera del perímetro de R-1 (recomendación R-2) |

H2 y R2 los comprobé en Chrome headless con una página mínima. El estilo
calculado es `display=none` y `visibility=collapse`, así que los dos
esconden el elemento. **No bloquean**:

- R-1 era una recomendación;
- el test implementa exactamente el perímetro que yo propuse (`hidden`,
  `none` en minúsculas);
- hoy `styles.css` no contiene nada de eso.

### 4 · Barrido de las 37 directivas nuevas, una mutación por aparición

**Recuento.** Lo recalculé con mi propio script (`directivas.py`,
`html.parser`, multiconjunto de `(atributo, expresión normalizada)`, sin
`x-cloak`), comparando `6bc4b6c` con `HEAD`:

- **37 nuevas**: 16 `:class`, 5 `:data-estado`, 6 `x-show` de vacío y de
  lista, 1 `x-show` de errores, 2 chips y 7 `x-text` de ficha. Coincide con
  la tabla del informe, clase a clase y línea a línea.
- **21 quitadas**:
  - 14 `:class`: las 11 de las pestañas y 3 sustituidas por `rs-*`;
  - 7 `x-text` con paréntesis.

  El informe solo nombra las 11 que se quitan sin sustituto. Es una
  imprecisión menor y no cambia la clasificación.

**Barrido** (`barrido4.py`). Una mutación por aparición:

- `x-show`: se niega o se le quita la negación;
- `:data-estado`: se fija a `'SAT'`;
- `:class`: se cambia por `''`;
- `x-text` de la ficha: se apunta a otra ficha.

| Clase | Resultado del barrido | ¿Consta en el informe? |
|---|---|---|
| `:data-estado` (335, 516, 630, 659, 889) | **5/5 muertos** | Sí («Muertas»). Correcto |
| `x-show` del **vacío** negado (349, 639, 893) | **3/3 muertos** (R58 `[bandeja/incidencias/impresion]`) | Sí. Correcto |
| `x-show` de la **lista** negado (298, 599, 882) | **3/3 SOBREVIVEN** | **No.** El informe dice «Muertas» por P2 (`x-show="true"`), que sí cae porque quita el nombre de la función. La negación la conserva y pasa |
| `x-show` de los errores (229) | muerto | Sí |
| `:class` (317, 374, 681, 834–836, 937, 941, 942, 1037) | sobreviven | Sí: supervivientes visuales (P4–P6 y S3), con su análisis |
| `x-text` de la ficha (179, 214, 239, 247, 458, 541, 797, 845, 900, 988) | sobreviven | Sí: la clase S2, con su análisis (ligadura anterior al bloque 5, O-2 de la review 3) |

**Comprobación en Chrome** (`chrome4.py`, Chrome headless con `--dump-dom`,
servidor local parado al terminar). Estado de la lista y del vacío en cada
sección:

```
original    #/impresion   {'lista': {'oculto': False, 'li': 13}, 'vacio': {'oculto': True, 'li': 0}}
original    #/incidencias {'lista': {'oculto': False, 'li': 19}, 'vacio': {'oculto': True, 'li': 0}}
882 negada  #/impresion   {'lista': {'oculto': True, 'li': 13}, 'vacio': {'oculto': True, 'li': 0}}
599 negada  #/incidencias {'lista': {'oculto': True, 'li': 19}, 'vacio': {'oculto': True, 'li': 0}}
```

**Cómo se lee**: con la lista negada, las filas están en el DOM pero la
lista se oculta. El vacío también queda oculto, así que la sección no enseña
**nada**.

Con cero filas pasaría lo contrario: la lista vacía se muestra junto al
estado vacío. Ninguno de los dos casos es equivalente.

La 298 (bandeja) tiene el mismo mecanismo y sale del mismo test
parametrizado.

**La causa** está en `services/postventa-front/tests/test_f035_portal.py:1761-1763`.
El test de R58 exige que algún ancestro de la plantilla tenga `funcion` en su
`x-show`, pero no comprueba la polaridad:

```python
contenedores = [a for a in plantilla.ancestros() if funcion in a.atributos.get("x-show", "")]
```

A la condición del vacío, dos líneas más arriba (1752), sí se le exige la
forma exacta.

### 5 · Campaña del arnés

- **Alcance.** `harness.alcance.alcance_de_feature('F-035')` da
  `lineas = {}`, con origen `rama` y `54c0884..feature/F-035-portal-posventa`.
- **Informe.** `progress/mutacion_F-035.md` declara 0 mutantes y
  «Tiempo total 0.0 s».
- **Reejecución.** Como son menos de 5 minutos, reejecuté la campaña entera:
  `python -m harness.mutacion --feature F-035 --salida <scratchpad>/mutacion_rev4.md`.
  Da 0 mutantes, 0 muertos, 0 supervivientes y 0 timeouts, los mismos
  totales. Después `git status` quedó limpio.
- **Control del cero.** Lo hice en la review 3: 477 mutantes, todos en
  tests. Este rango solo añade tests, así que el cero sigue siendo por
  diseño.

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
- [x] La primera línea con la ruta sigue en `test_f035_portal.py` y en los
  dos `.md`.
- [x] Sin `print` de depuración, sin TODO y sin secretos.
- [x] Sin dependencias nuevas.
- [x] Checkpoints de dominio (parte, firma, `conest`…): **N/A**. El rango no
  toca lógica del circuito, porque el diff no incluye ningún fichero de
  producción.
- [x] Ningún PDF ni parte escaneado en git.

**C3 bis**

- [x] **N/A**: el rango no toca `docs/referencia/`.

**C4**

- [ ] **Cada requisito tiene un test trazable que lo verifica.** R55 ya ve
  la especificidad (G y G2 caen). **Pero R58 no ve que la lista se esconda
  cuando hay filas**: las mutaciones 298, 599 y 882 sobreviven, y lo
  comprobé en Chrome. Es el cambio requerido 1.
- [x] Los tests unitarios no tocan red ni BBDD.
- [x] Las verificaciones MANUAL tienen su guion (bloque 5b §9). **T12, con
  V1 y V2 del humano, sigue pendiente.** No es un fallo del implementer.

**C4 bis**

- [x] `rigor: estandar` declarado.
- [x] **Fase RED: N/A justificado.** Los 6 tests nuevos cierran huecos de
  prueba sobre un comportamiento que ya era correcto. Sin una mutación
  delante no hay rojo posible. Su «rojo» son las trazas de mutación del
  informe, que he reproducido yo (§3).
- [x] **Cobertura: N/A**, con el motivo impreso por `init.sh`.
- [x] **Mutación**: 0 mutantes, comprobados con el alcance recalculado y
  con la reejecución.
- [x] **Muertos comprobados**: 0.0 s declarados, así que reejecuté la
  campaña. Mismos totales y árbol limpio.
- [x] **Coste por mutante: N/A**, porque no hay ningún mutante.
- [ ] **Supervivientes analizados.** Los de la campaña: ninguno. En las
  mutaciones a mano que compensan (D-9), 298, 599 y 882 **sobreviven, no son
  equivalentes y no están documentados**. Además, el informe da su clase
  como «Muertas». Es el cambio requerido 1.
- [x] Las «Evidencias» de esta vuelta traen los cuatro números.
- [x] Ningún N/A va sin su motivo.

**C4 ter**

- [x] **N/A**: `harness/rutas_sensibles.json` no existe.

**C5**

- [x] En `tasks.md`, T14–T19 siguen `[x]` y T12 `[ ]`, por diseño (humano).
  Esta vuelta no abre tareas: el commit `ecf0c2f` es la corrección de la
  review, con el mismo formato que en las vueltas anteriores.
- [x] No hay ficheros temporales ni sin trackear, y el árbol está limpio.
- [x] `features.json` dice `in_progress`, que es el estado real.

## Cobertura: requisito → test (lo que cambia en esta vuelta)

| R | Test nuevo | Estado |
|---|---|---|
| R55 | `test_f035_r55_el_movimiento_reducido_gana_por_especificidad[styles.css, portal.css]` | verde; caza G, G-portal y G2 |
| R40 (chips del volcado) | `test_f035_r40_cada_chip_del_volcado_va_en_su_panel` | verde; caza S1 y S1b |
| §5.2 (errores de la importación) | `test_f035_entrada_la_lista_de_errores_de_la_importacion_se_ve_cuando_hay_errores` | verde; caza O2 (y O) |
| R57 | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` | verde; caza DE y los 5 `:data-estado` |
| R60 / R-1 | `test_f035_r60_styles_css_no_puede_esconder_ni_desactivar_el_circuito` | verde; caza H, I y R (no H2 ni R2, ver R-2) |
| R58 | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[×3]` | verde, pero **no ve la lista negada** (cambio 1) |

El resto de R48–R61 no cambia desde la review 3: sigue en verde con los
mismos tests.

## Cambios requeridos

1. **R58: exigir la polaridad del `x-show` de la lista.** En
   `services/postventa-front/tests/test_f035_portal.py:1761-1763`
   (`test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla`),
   el contenedor de la lista tiene que cumplir, como el vacío en la
   línea 1752, una forma exacta. Con los blancos quitados, su `x-show` debe
   ser `f"{funcion}.length"` o `f"{funcion}.length>0"`. Que contenga
   `funcion` no basta.

   **Verificación**: en una copia desechable, estas tres negaciones tienen
   que dar **rojo**, cada una en su parámetro de R58:
   - `x-show="!bandejaFiltrada().length"` en `index.html:298`;
   - `x-show="!incidenciasFiltradas().length"` en `index.html:599`;
   - `x-show="!impresionFiltrada().length"` en `index.html:882`.

   Pega las trazas en el informe.

2. **Corregir la fila «`x-show` de estado vacío y de lista» de la tabla P-R1**
   en `progress/impl_F-035.md`, en el apartado «Correcciones de la
   review 3» §3. Hay que añadir la negación de la lista como mutación de la
   clase, con su resultado tras el cambio 1.

Solo toca el test y el informe. Ni `partes.html`, ni `index.html`, ni
`css/*.css`, ni `js/*.js`. Después, `bash harness/init.sh` tiene que seguir
en verde.

## Recomendación (no bloquea)

**R-2 · Cerrar los dos flancos que R-1 deja abiertos.** En
`test_f035_r60_styles_css_no_puede_esconder_ni_desactivar_el_circuito`:

- **Comparar el valor en minúsculas.** Las palabras clave de CSS no
  distinguen mayúsculas: `display: NONE` esconde, y hoy pasa (H2).
- **Tratar `visibility: collapse` igual que `hidden`.** Fuera de tablas
  esconde igual (R2).

Lo comprobé en Chrome: los dos esconden el elemento. Cuesta dos líneas, y
puede ir en el mismo encargo si el líder quiere.

## Observaciones

- **O-1**: T12 (V1 y V2 del humano, guion en el bloque 5b §9) sigue
  pendiente. F-035 no se puede cerrar hasta que el humano la haga y la anote
  en `current.md`. No cuenta como fallo del implementer.
- **O-2**: el informe dice que el bloque «quitó 11 `:class`». En realidad se
  quitan 21 directivas:
  - 14 `:class`: 11 sin sustituto y 3 cambiadas por su versión `rs-*`;
  - 7 `x-text` con paréntesis.

  Las sustituidas ya cuentan entre las 37 nuevas, así que no cambia nada.
  Anótalo al tocar esa sección.

## Automejora (propuesta, no aplicada)

**P-R3** · para `.claude/agents/reviewer.md` y `CHECKPOINTS.md` C4 bis, y de
ahí a `arnes-base`. Complementa P-R2.

- **Una mutación por aparición, no una por clase.** En P-R1, cuando las
  directivas nuevas se cuentan por decenas, «una por clase» deja pasar
  operadores que la muestra no probó. El caso de origen es este: P2
  (`"true"`) murió, pero la negación sobre el mismo atributo sobrevive.
- **Un barrido mecánico es barato.** Bastan los operadores básicos (negar
  `x-show`, fijar `:data-estado`, vaciar `:class`, cruzar `x-text`) sobre
  cada aparición: aquí fueron unos 5 minutos.
- **Para el `x-show`, la negación siempre.** Es el operador que distingue
  «el test mira la expresión» de «el test mira su sentido».

Caso de origen: F-035, review 4, con las mutaciones de las líneas 298, 599
y 882.
