<!-- progress/review3_F-035.md -->
# F-035 · Review 3 · Enmienda del estilo Ruesma (bloque 5, T14–T19)

> Revisado el **2026-09-25** sobre `feature/F-035-portal-posventa`, commit
> `4d43bbd`, rango `6bc4b6c..4d43bbd` (lo anterior se aprobó en la review 2).
> Referencias: `requirements.md` R48–R61, `design.md` §13.1 «Segunda ronda» y
> §15, el acta del bloque 5 en `tasks.md` e `impl_F-035.md`, «Bloque 5a» y
> «Bloque 5b».
>
> **En esta revisión no se ha implementado ni corregido nada.** Mis
> mutaciones se aplicaron en un worktree desechable del scratchpad
> (`git worktree add -b feature/F-035-rev3-tmp`, con el prefijo de rama para
> que corran los tests de rama). Cada mutante se restauró con `git checkout`.
> Al terminar, `git status` del worktree estaba vacío, se hizo
> `git worktree remove` y `git branch -D`. El árbol real sigue limpio: el
> único fichero que escribo en él es este, y no lo commiteo.

## Veredicto

**CHANGES_REQUESTED** (RECHAZADO).

**Lo que importaba más está bien, y lo he comprobado yo:**

- El circuito en producción solo cambia de presentación.
- La guardia R59 caza todo lo que le he tirado.
- `styles.css` no puede tapar ni desactivar hoy nada del circuito.
- El contraste AA lo calcula un test.
- No hay datos personales.

**Por qué rechazo.** Hay tres huecos en las pruebas: los tres son mutantes
**no equivalentes** que sobreviven y que el informe no recoge. Uno de ellos
deja **R55 sin vigilar**: con el movimiento reducido, la suite sigue en verde
aunque el pulso y las transiciones sigan en marcha, y lo he comprobado en
Chrome. Los otros dos son ligaduras que añade el bloque 5 y que nadie mutó.
Arreglarlos cuesta poco: ver «Cambios requeridos».

## Nivel de rigor

`estandar` (`harness/features.json`, declarado). Exige:

- fase RED en los requisitos centrales;
- cobertura de las líneas cambiadas;
- campaña de mutación, con los supervivientes documentados y analizados (el
  reviewer juzga).

El bloque 5 no cambia Python de producción. Por eso la cobertura sale en N/A
con su motivo y la campaña da 0 mutantes. Lo que compensa son las mutaciones
a mano (D-9, `design.md` §11, recuadro de la segunda ronda) y las mías de
abajo.

## Verificación ejecutada por el reviewer

### 1 · `bash harness/init.sh`

Lo ejecuté tal cual y terminó en **ENTORNO LISTO**:

- raíz: **73 passed**;
- servicio `front`: verde (la caché del árbol ya estaba en verde);
- worktree limpio: **346 passed**, que incluye el puente con los 409 tests
  de JavaScript;
- `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`;
- `ruff`: 61 avisos, la misma deuda de antes.

### 2 · El circuito solo cambia de presentación (comparación propia)

Escribí mi **propio comparador**, sin reutilizar el `tokens()` del
implementer:

- lee el HTML con `html.parser`;
- conserva todos los atributos en su orden, **incluidas las `:class`**, y
  quita solo `class`;
- normaliza los blancos del texto y compara con `difflib`;
- lo aplico entre `54c0884:services/postventa-front/index.html` (la base =
  `git merge-base dev HEAD`) y `HEAD:services/postventa-front/partes.html`.

Sale **exactamente** esto y nada más:

| Diferencia | Detalle |
|---|---|
| Token 0 (la línea 1) | Comentario `…/index.html` → `…/partes.html` |
| 4 `<link>` insertadas | Las de §15.4, exactas, en el `<head>`, justo antes de `css/styles.css` (líneas 13–17) |
| Barra insertada | El comentario, luego `<nav data-barra-portal>` hasta `</nav>`, como primer hijo del `<div x-data="appPostventa()">` |

**Directivas y atributos.** 506 tokens en la base y 552 en `HEAD`, que son
la base + 4 `<link>` + 42 de la barra. Las 199 etiquetas de apertura
emparejadas tienen la misma lista de atributos **en el mismo orden**,
contando también el sitio del `class`: no se añadió ni se quitó ningún
`class`.

**Clases con comportamiento.** Cambian 92 valores de `class`. Se conservan
los dos `hidden` de los `<input type="file">`. El único cambio que parece
de comportamiento es `overflow-hidden` en la barra de progreso, y lo recoge
`.rs-progreso { overflow: hidden }`. `text-red-800` se conserva en el aviso
de fallo del autoguardado, **detrás** de su `x-show`.

**Ficheros que no cambian en el rango.** `git diff --name-status 6bc4b6c..HEAD`
sale **vacío** para:

- `services/postventa-front/js`;
- `staticwebapp.config.json`, `dev_server.py`, `dev_front.ps1`;
- `infra`;
- `services/postventa-api`.

En `tests/` y `tests_js/` del front solo cambian `test_f035_portal.py` y
`tests_js/portal.test.js`, los dos de F-035. Ningún test del circuito cambia
en este rango.

**Tests de F-035 que cambian.** En `tests_js/portal.test.js` solo hay altas.
En `test_f035_portal.py` las únicas líneas quitadas son el test de `difflib`
de R30/R43, que sustituye R59 como pide la spec. R32 (las siete líneas
`INDEX`) sigue en verde sobre la rama entera.

### 3 · He roto la guardia R59 en la copia desechable

`partes.html` **no tiene ningún atributo `id`**, así que en lugar de un `id`
quité un `x-show`, añadí atributos y cambié textos:

| Mutación en `partes.html` | Resultado | Lo mata |
|---|---|---|
| A · quitar `x-show="avisoArchivo"` | **rojo** (1 fallo) | R59 de rama |
| B · `:class` del semáforo sin `ring-2 …` | **rojo** (3 fallos) | R59, `test_f026_front.py:296`, `test_f028_front.py:536` |
| C · `aria-label` nuevo en «Cerrar» | **rojo** (2 fallos) | R59; y además el control permanente, que ya no encuentra su cadena |
| D · «Cancelar» → «Cancela» | **rojo** | R59 |
| E · una quinta `<link>` tras las de la marca | **rojo** (2 fallos) | R59 y R50 |

### 4 · ¿Puede `css/styles.css` ocultar o cambiar el comportamiento del circuito?

Leí la hoja entera (841 líneas) y la contrasté con los elementos del
circuito. **Hoy no puede.**

- **`!important`**: no hay ninguno en `styles.css`. En `portal.css` solo
  está el de `[x-cloak]`, y el circuito no carga esa hoja. Lo vigila R60.
- **`display` frente a `x-show`**: Alpine esconde con un `style` en línea,
  así que ninguna regla sin `!important` puede mostrar lo que `x-show`
  oculta. Tampoco hay ninguna que oculte lo que `x-show` enseña: el único
  `display: none` es el de `.rs-barra__sep` y `.rs-barra__etiqueta` por
  debajo de 560 px, que son decorativos y están dentro de la barra. Las
  reglas `display: flex/block/inline-flex` de `.rs-btn`, `.rs-fila`,
  `.rs-rotulo`… solo se aplican cuando Alpine quita el `display: none`.
- **`pointer-events`, `visibility`, `opacity: 0` estático, `content-visibility`**:
  no aparecen en ninguna de las dos hojas.
- **`position`**:
  - `.rs-barra` es `sticky` con `z-index: 30`, y el circuito no tiene nada
    `fixed` ni `absolute` que pueda quedar debajo.
  - `.rs-panel--destacado` es `relative` con `overflow: hidden`, pero la
    pregunta de confirmación va dentro, en el flujo normal (no es un
    desplegable), así que no se recorta.
  - `.rs-panel--lista` lleva `overflow: hidden`, y la lista no tiene nada
    posicionado.
- **`x-cloak` y `x-transition`**: el circuito no usa ninguno. Retirar la
  regla vieja de `styles.css` no le afecta.
- **Foco**: ni `partes.html` ni `index.html` llevan `outline-none` ni
  `focus:`, así que el `:focus-visible` global no lo tapa ninguna utilidad.

Lo que **no** vigila ningún test está en R-1, más abajo, como recomendación.

### 5 · Contraste, foco y movimiento reducido

- **Contraste AA (R53).** `test_f035_r53_los_pares_de_la_marca_cumplen_aa`
  recalcula los 21 pares desde el `:root`, con la fórmula WCAG. Esa fórmula
  la comprueba a su vez `test_f035_r53_la_formula_de_contraste_es_la_de_wcag`
  (21:1, 1:1 y el 3,73 del acero). Lo comprobé con dos mutaciones:
  - J, `--rs-atencion: #d97706`: **rojo** en R53 y en R49;
  - la 12 del implementer (el acero como texto): también cae.
- **Foco (R54).** Mutación K, que quita el `outline` de `:focus-visible`:
  **rojo**.
- **Movimiento reducido (R55).** La hoja lo hace bien, y lo he visto en
  Chrome headless con `--force-prefers-reduced-motion`:
  - `.rs-paso` queda con `animationName=none`;
  - `.rs-btn` queda con `transitionDuration=0s`.

  **Pero ningún test lo protege: es el cambio requerido 1.**

### 6 · Sin datos personales

- **Altas del rango**: solo `.gitattributes` y los dos SVG. Los dos tienen
  los SHA-256 de §15.4, recalculados en el worktree, que es un checkout
  nuevo, así que el `.gitattributes` funciona. No entra ninguna captura, ni
  PDF, ni imagen rasterizada.
- **Barrido de las líneas añadidas en el rango**, con estos patrones:
  - DNI y NIE: `\b[0-9]{8}[A-Za-z]\b`, `\b[XYZ][0-9]{7}[A-Za-z]\b`;
  - correo: `…@…\.[a-z]{2,}`;
  - IPv4 y teléfono: `\b[6789][0-9]{8}\b`;
  - GUID;
  - `password`, `secret`, `api_key`, `AccountKey`, `DefaultEndpoints`,
    `sig=`.

  Resultado: **ninguna coincidencia**, descontados los decoradores
  `@pytest`.
- **Informes**: solo nombran `muestras/` en el guion de V2 (en local, sin
  versionar). Las capturas del implementer usaron datos ficticios
  («EJEMPLO VILLA 001», `EJ-0001`, DNI «(ejemplo)») y no están en el
  repositorio.

### 7 · Campaña del arnés, verificada por mi cuenta

- **Alcance.** `harness.alcance.alcance_de_feature('F-035')` da
  `lineas = {}`, con origen `rama` y `54c0884..feature/F-035-portal-posventa`.
  Coincide con el informe: 0 ficheros y 0 líneas.
- **Control del cero.** Pasé `generar_mutantes` sobre todas las líneas
  Python del diff, **sin filtro de producción**:
  - 477 mutantes en total;
  - 426 en `test_f035_portal.py` y 51 en `tests/test_f035_placeholders_vivos.py`;
  - 0 en las siete líneas `INDEX`.

  El generador funciona, así que el cero se debe a la exclusión por diseño:
  en Python solo cambian tests.
- **Reejecución.** El informe declara «Tiempo total: 0.0 s», que es menos de
  5 minutos, así que la reejecuté entera con
  `python -m harness.mutacion --feature F-035 --salida <scratchpad>/mutacion_rev3.md`.
  Da los mismos totales: 0 mutantes, 0 muertos, 0 supervivientes y
  0 timeouts. `git status` quedó limpio.
- **Coste por mutante**: no aplica, porque no hay ningún mutante.

### 8 · Mutaciones a mano: las del implementer y las mías

El implementer mutó 17 veces:

- las cinco de §11 (9–13): 5/5 muertas;
- la guardia: 4/4;
- la categoría P-R1: 5 de 8, con P4, P5 y P6 como supervivientes **no
  equivalentes**. Lo comprobó ejecutándolas: con `--dump-dom`, contó las
  clases pintadas.

Con esas tres estoy de acuerdo. Son puro aspecto de la maqueta y quedan
documentadas con su análisis, que es lo que pide `estandar`. No declara
**ningún equivalente**.

Las mías, además de A–E:

| Mut. | Fichero | Cambio | Resultado |
|---|---|---|---|
| J | `styles.css` | `--rs-atencion: #d97706` | muerto (R49, R53) |
| K | `styles.css` | `:focus-visible` sin `outline` | muerto (R54) |
| L | `styles.css` | `.rs-pestana[aria-current="page"]` → `.rs-pestana.actual` | muerto (R51) |
| Q | `styles.css` | `transition: width 200ms` en `.rs-progreso__barra` | muerto (R55) |
| M | `index.html` | el vacío de la bandeja con el `x-show` al revés | muerto (R58) |
| N | `index.html` | `:data-estado` del volcado fijo en `'creado'` | muerto (R57, JS) |
| P | `portal.css` | sin la regla `[data-estado="SAT"]` | muerto (R57, JS) |
| **G** | `styles.css` | `:is(*, #rs-movimiento-reducido)` → `*` en el bloque `prefers-reduced-motion` | **superviviente, NO equivalente** |
| **S1** | `index.html:489` | el chip «Simulación» con `x-show="r.resultado === datos.volcado.hecho"` | **superviviente, NO equivalente** |
| **O2** | `index.html:229` | la lista de errores de la importación con `x-show="!datos.entrada.errores.length"` | **superviviente, NO equivalente** |
| O | `index.html:229` | ese mismo `x-show` a `"true"` | superviviente, **equivalente** |
| S2 | `index.html` | `x-text="datos.capitulos.ficha"` → `datos.entrada.ficha` | superviviente (ver O-2) |
| S3 | `index.html` | la `:class` de la nota de motivo del capítulo → `''` | superviviente, visual (como P4–P6) |
| H | `styles.css` | `.rs-aviso--info { display: none; }` | superviviente (R-1) |
| I | `styles.css` | `pointer-events: none` en `.rs-btn` | superviviente (R-1) |
| R | `styles.css` | `visibility: hidden` en `.rs-panel--destacado` | superviviente (R-1) |

**Cómo comprobé cada motivo, ejecutándolo:**

- **G, no equivalente.** Chrome headless con `--force-prefers-reduced-motion`
  y una página de prueba que carga la hoja:
  - hoja original: `reduce=true paso.animationName=none btn.transitionDuration=0s`;
  - hoja mutada: `reduce=true paso.animationName=rs-paso-pulso btn.transitionDuration=0.18s`.

  Con el selector universal `*`, de especificidad (0,0,0), las reglas de
  clase (0,1,0) le ganan. Con el movimiento reducido, el pulso del circuito
  y todas las transiciones siguen en marcha, y R55 no se cumple. El test
  `test_f035_r55_prefers_reduced_motion_lo_apaga_todo` solo mira que exista
  una regla con `*`, `transition: none` y `animation: none`, así que pasa
  igual.
- **S1 y O2, no equivalentes.** Serví el portal del worktree y lo abrí en
  Chrome headless (`--dump-dom`), en `#/bandeja` y `#/entrada`.
  - **Original**: el chip «Simulación» se ve en el panel de dry-run y está
    oculto en el del volcado hecho; la lista de errores se ve.
  - **Con S1 y O2**:
    - «Simulación» sale oculto en el dry-run y **visible en el volcado
      hecho**, junto a «Hecho en Sigrid»;
    - la `<ul>` de errores queda **oculta** (`display: none`), aunque
      «Fila 7» sigue en el DOM.
- **O, equivalente.** `datos` es `window.MaquetaDatos` (`portal_app.js:21`).
  Además, `datos.entrada.errores` solo se define en `maqueta_datos.js:132`,
  con 2 filas, y ningún código lo cambia (lo busqué con `grep`). En el
  render original la lista se ve, igual que con `"true"`.

**La categoría P-R1 queda incompleta.** El informe dice que se mutó «una de
cada clase de ligadura». Frente a `6bc4b6c`, el bloque 5 añade 33 directivas
en `index.html`, y las cuento abajo. Los `x-show` de los chips del volcado
(S1) y de la lista de errores (O/O2) son clases que no se mutaron, y sus
supervivientes no están documentados.

## Checkpoints

**C1**

- [x] `bash harness/init.sh` termina con exit 0.
- [x] Existen los ficheros del arnés.

**C2**

- [x] Una sola feature `in_progress` (F-035).
- [x] La rama es `feature/F-035-portal-posventa`.
- [x] `current.md` solo habla de F-035. Sigue acumulando bloques anteriores:
  es la deuda O-2 de la review 1, no bloquea.
- [x] Toda feature `done` tiene su resumen en `history.md` (sin cambios en
  el rango).

**C3**

- [x] Hexagonal: **N/A**. El bloque solo toca el front estático (HTML, CSS,
  SVG y tests), sin dominio ni adaptadores.
- [x] Primera línea con la ruta en todos los ficheros de texto nuevos o
  modificados: CSS, HTML, `.gitattributes` y tests. Los SVG van sin ella a
  propósito, porque son copias byte a byte (R52).
- [x] Sin `print` de depuración, sin TODO sin contexto y sin secretos.
- [x] Dependencias nuevas: solo Google Fonts por CDN, que está prevista y
  decidida por el humano (tasks.md, bloque 5).
- [x] Parte como unidad, validaciones antes de archivar, lo manuscrito,
  firmado frente a conforme, reprocesar sin duplicar y `conest`: **N/A**.
  El bloque 5 no toca la lógica del circuito, y lo he comprobado (R59, §2 de
  esta review).
- [x] Ningún PDF ni parte escaneado en git: las únicas altas son
  `.gitattributes` y los dos SVG.

**C3 bis**

- [x] **N/A**: el rango no añade ni modifica nada en `docs/referencia/`.

**C4**

- [ ] **Cada requisito tiene un test trazable que lo verifica.** Hay un test
  para cada uno de R48 a R61 (tabla de abajo) y todos pasan. **Pero el de
  R55 no detecta que el bloque de movimiento reducido pierda**: mutante G,
  comprobado en Chrome. Cambio requerido 1.
- [x] Los tests unitarios no tocan red ni BBDD: son lecturas de ficheros y
  git local.
- [x] Las verificaciones MANUAL del humano (V1, V2 y V4) tienen guion
  exacto en `impl_F-035.md` §9 del bloque 5b, y `current.md` remite a él.
  T12 sigue `[ ]`: es tarea del humano.

**C4 bis**

- [x] `rigor: estandar` declarado.
- [x] **Fase RED**: hay trazas reales de T14, T15, T16 (3), T17 y R57 (JS).
  R59 no puede tener fase RED, porque es una guardia que acepta el estado
  aprobado. Su prueba es el control permanente y las mutaciones 9, 10 y
  G1–G4, que he visto caer y he reforzado con A–E.
- [x] **Cobertura**: `N/A` con su motivo impreso por `init.sh`.
- [x] **Mutación**: `progress/mutacion_F-035.md`, con 0 mutantes. Lo
  verifiqué con el alcance recalculado y con el control sin filtro de
  producción (477 mutantes).
- [x] **Muertos comprobados**: 0.0 s, que es menos de 5 minutos, así que
  reejecuté la campaña: mismos totales y árbol limpio.
- [x] **Coste por mutante**: N/A, porque no hay ningún mutante.
- [ ] **Supervivientes analizados.** Los de la campaña: ninguno. Los de las
  mutaciones a mano, que compensan (D-9): **G, S1 y O2 sobreviven, no son
  equivalentes y no están documentados.** Cambios requeridos 1, 2 y 3.
- [x] Hay «Evidencias» con los cuatro números y los workers (1 en la
  campaña).
- [x] Ningún N/A de este bloque va sin su motivo.

**C4 ter**

- [x] **N/A**: `harness/rutas_sensibles.json` no existe y la puerta no
  señaló ninguna ruta.

**C5**

- [x] En `tasks.md`, T14–T19 están `[x]`, con los commits `F-035 T14`
  `83cb64f`, `T15` `b3ebbe9`, `T16` `4cb0603`, `T17` `bf8d45e`, `T18`
  (`25a708d`, `1cbc1ea`, `05ead04`) y `T19` `d5f38cd`. T12 queda `[ ]` por
  diseño (V1 y V2 del humano, después de T19).
- [x] No hay ficheros temporales ni sin trackear. El worktree
  `.claude/worktrees/agent-a6e2f9bed1d46cdbc` ya existía y no es de este
  bloque.
- [x] `features.json` dice `in_progress`, que es el estado real.

## Cobertura: requisito → test

| R | Test(s) | Estado |
|---|---|---|
| R48 | `tests/test_f035_placeholders_vivos.py`: `…r48_las_secciones_reales_se_abren_en_la_misma_ventana`, `…r48_la_guardia_mira_una_seccion_que_pasa_a_real`, `…r48_inicio_es_real_cuando_lo_son_todas_las_demas`, `…r48_la_regla_consta_en_architecture_y_en_el_readme_del_front` | verde (11 passed en la raíz) |
| R49 | `…r49_los_tokens_de_la_marca_estan_en_el_root_con_su_valor`, `…r49_fuera_del_root_solo_hay_colores_sombras_y_radios_de_token[×2]` | verde |
| R50 | `…r50_la_pagina_carga_las_fuentes_y_el_favicon_antes_de_la_hoja[×2]`, `…r50_la_base_da_la_fuente_la_trama_y_los_titulares` | verde |
| R51 | `…r51_la_barra_lleva_logo_separador_y_etiqueta_sin_enlace[×2]`, `…r51_las_pestanas_son_rs_pestana_sin_class_dinamico[×2]`, `…r51_la_pestana_actual_la_pinta_aria_current_en_la_hoja`, `…r51_cada_pestana_de_la_barra_marca_su_propia_seccion`, `…r51_cada_pestana_de_la_ficha_se_marca_a_si_misma` | verde |
| R52 | `…r52_los_svg_son_copias_exactas_de_front_portal[×2]`, `…r52_los_svg_no_llevan_nada_activo_ni_colores_ajenos[×2]` | verde |
| R53 | `…r53_la_formula_de_contraste_es_la_de_wcag`, `…r53_los_pares_de_la_marca_cumplen_aa`, `…r53_el_acero_no_se_usa_como_color_de_texto[×2]` | verde |
| R54 | `…r54_hay_un_foco_visible_en_burdeos`, `…r54_ninguna_regla_quita_el_contorno_sin_poner_otro[×2]` | verde |
| R55 | `…r55_las_transiciones_son_cortas_y_sobre_lo_permitido[×2]`, `…r55_las_animaciones_son_de_entrada_y_del_portal[×2]`, `…r55_prefers_reduced_motion_lo_apaga_todo[×2]` | verde, pero **no ve el mutante G** (cambio 1) |
| R56 | `…r56_en_el_portal_el_discontinuo_y_la_marca_no_se_mezclan_con_los_placeholders`, `…r56_en_portal_css_el_discontinuo_es_de_los_placeholders_y_sin_burdeos`, `…r56_el_aviso_de_maqueta_no_usa_el_burdeos`, `…r56_el_circuito_no_tiene_placeholders` | verde |
| R57 | `tests_js/portal.test.js`: «f035 R57: cada código de estado … tiene su regla [data-estado]», «… todo elemento … con data-estado es un rs-chip con su texto», «… ningún estado se pinta fuera de su chip» | verde |
| R58 | `…r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[bandeja, impresion, incidencias]` | verde |
| R59 | `…r59_partes_html_solo_cambia_en_presentacion_frente_a_la_base` (rama), `…r59_control_el_circuito_real_contra_si_mismo_no_da_diferencias`, `…r59_control_la_guardia_rechaza_lo_que_no_es_presentacion[×8]`, `…r59_control_la_barra_tiene_que_ser_el_primer_hijo_del_circuito`, `…r59_control_la_guardia_acepta_un_class_cambiado` | verde; A–E los caza |
| R60 | `…r60_las_hojas_no_llevan_important_import_ni_data[×2]`, `…r60_el_circuito_no_lleva_style_estatico` | verde |
| R61 | `…r61_el_readme_explica_la_identidad_visual` | verde |
| R33 (enmendado) | `…r33_no_se_modifica_nada_del_circuito` (admite `M css/styles.css`) | verde |

## Desviaciones del implementer: las acepto

1. **`.gitattributes` nuevo** (`img/*.svg -text`). Está medido y justificado,
   y lo he confirmado: en el worktree, que es un checkout nuevo, los SVG
   salen con su SHA-256.
2. **R59 conserva el sitio del `class`.** Es más estricto que la letra de
   §15.8, y es lo que permite cazar la mutación 10. Correcto.
3. **R55 acota a 250 ms las transiciones, no las animaciones.** Es lo que
   dice el requisito, y §15.5 pide 420 ms para la entrada de las tarjetas.
   Correcto.
4. **`:is(*, #rs-movimiento-reducido)` en lugar de `!important`.** Es una
   buena solución y funciona, lo vi en Chrome. Lo que falta es que la
   vigile un test (cambio 1).

## Cambios requeridos

1. **R55: que el test vea que el movimiento reducido gana de verdad.** En
   `services/postventa-front/tests/test_f035_portal.py:1531-1545`
   (`test_f035_r55_prefers_reduced_motion_lo_apaga_todo`), además de que
   exista la regla universal, exigir que su selector **gane por
   especificidad** a toda regla de la misma hoja que declare `animation*` o
   `transition*`. Dos formas de hacerlo:
   - la sencilla: exigir que el selector universal sea
     `:is(*, #<id>)` (regex `:is\(\s*\*\s*,\s*#[\w-]+\s*\)`) y que ninguna
     regla con `animation*` o `transition*` de las dos hojas use un
     selector de id;
   - o calcular la especificidad.

   **Verificación**: en una copia desechable, sustituir en `css/styles.css`
   las tres apariciones de `:is(*, #rs-movimiento-reducido)` por `*` (mi
   mutante G) tiene que dar **rojo**, y lo mismo en `css/portal.css`. Pega
   las trazas en el informe.
2. **Los chips del volcado: que cada uno esté en su panel.** En
   `services/postventa-front/index.html:489-490`, el chip «Simulación» va con
   `datos.volcado.dryRun` y «Hecho en Sigrid» con `datos.volcado.hecho`.
   Hoy se pueden cruzar y el volcado hecho sale etiquetado como
   «Simulación» (mutante S1, comprobado en Chrome), en un proyecto cuya
   regla central es «dry-run siempre primero».

   Añade un test en `tests/test_f035_portal.py` que fije la condición
   `x-show` de cada chip con su texto. Si decides que no merece test,
   documéntalo como superviviente con su análisis en el informe. Prefiero
   el test.

   **Verificación**: el mutante S1 tiene que dar rojo, o constar en el
   informe con su análisis.
3. **Completar la categoría P-R1 del bloque 5 en `progress/impl_F-035.md`**
   (§7.b del bloque 5b). Hay que enumerar las **33 directivas nuevas** de
   `index.html` frente a `6bc4b6c` y, para cada **clase**, dar la mutación
   que la cubre o su análisis de superviviente. Sin eso, «una de cada clase»
   no se puede comprobar. Las clases son:
   - 15 `:class` de presentación;
   - 5 `:data-estado`;
   - 6 `x-show` de vacío y de lista;
   - el `x-show` de la lista de errores de la importación;
   - 2 `x-show` de los chips del volcado;
   - 7 `x-text` de la ficha F-0NN.

   Como mínimo:
   - **O2** (`index.html:229`, el `x-show` al revés esconde los errores de
     la importación; no es equivalente, lo vi en Chrome): con test o con su
     análisis de superviviente;
   - **O** (`"true"`): como equivalente, con el motivo que he comprobado.
     Los datos son estáticos, `datos.entrada.errores` tiene 2 filas en
     `maqueta_datos.js:132` y ningún código lo cambia;
   - **S1**: remite al cambio 2.

Ninguno toca `partes.html`, `css/styles.css` ni un `js/*.js`. Los cambios 1
y 2 solo añaden tests, y el 3 es del informe. Después, `bash harness/init.sh`
tiene que seguir en verde.

## Recomendación (no bloquea)

- **R-1 · Una guardia para que `styles.css` no pueda tapar el circuito.**
  - **Por qué**: `css/styles.css` lo carga ya el circuito en producción, y
    lo van a editar las fichas del portal.
  - **Qué pasa hoy**: R60 solo vigila `!important`. Tres mutantes míos
    pasan con la suite en verde: H (`display: none` en `.rs-aviso--info`),
    I (`pointer-events: none` en `.rs-btn`) y R (`visibility: hidden` en
    `.rs-panel--destacado`). Cualquiera de ellos escondería o desactivaría
    un aviso o un botón del circuito.
  - **Por qué no bloquea**: hoy la hoja está limpia, lo comprobé en §4, y
    ningún requisito lo pide.
  - **Propuesta**: un test que prohíba en `styles.css`:
    - `pointer-events`;
    - `visibility: hidden`;
    - `opacity: 0` fuera de `@keyframes`;
    - `display: none` fuera de pseudoelementos y de la regla de ≤ 560 px de
      la barra.

    Es barato y cubre el riesgo de §15.9 («una regla tapa un `x-show`») por
    los lados que R60 deja abiertos. Si el líder lo quiere, puede ir en el
    mismo encargo.

## Observaciones

- **O-1**: T12 (V1 y V2 del humano) sigue pendiente. F-035 no se puede
  cerrar hasta que el humano la haga y la anote en `current.md`.
- **O-2**: S2 (el `x-text` de la ficha F-0NN apuntando a otra ficha)
  sobrevive, pero la ligadura ya existía antes del bloque 5 (antes
  `'(' + … + ')'`). No es nueva; la anoto por si una ficha futura quiere
  fijar qué ficha construye cada panel.
- **O-3**: el mutante C hace caer también el control permanente de R59:
  «el control ya no encuentra una sola vez». Está bien que caiga, pero el
  motivo es frágil ante cualquier retoque de ese `<button>`. No hace falta
  tocarlo.

## Automejora (propuesta, no aplicada)

**P-R2 · para `.claude/agents/reviewer.md` y `CHECKPOINTS.md` C4 bis, y de
ahí a `arnes-base`.** Vale para cualquier front.

- **Ampliar P-R1 a las ligaduras del HTML.** Cuando una feature añade
  directivas de plantilla (Alpine, Vue…) sin tocar el componente, la
  compensación manual debe **enumerar** las directivas nuevas (diff de
  atributos `x-*`, `:*` y `@*` frente a la base) y mutar al menos una por
  cada clase. En el informe tiene que ir la tabla completa, no una muestra
  «representativa».
- **Probar las reglas de CSS que funcionan por especificidad** (un
  `:is(…, #id)`, una regla que tiene que ganar a una utilidad) en el
  navegador, o con un test que calcule la especificidad. Su mera presencia
  no demuestra nada.

Caso de origen: F-035, review 3, con los mutantes G, S1 y O2.
