<!-- progress/impl_F-040.md -->
# F-040 · Volcar a Sigrid las incidencias aprobadas — informe de implementación (desde el 2026-11-19)

Lo anterior (Bloque 0, Bloque 1, T4, T5.1, T5.2, T6a, hasta el aparcamiento del
2026-11-05) está en `progress/impl_F-040_hasta_2026-11-05.md`, renombrado con
`git mv` por la decisión D-8 (`specs/F-040-volcado-sigrid/design.md` §12): pasaba
de la puerta TAMAÑO (520/220).

## Base fija

- **`4b1eb21`** (rama `feature/F-040-volcado-sigrid`, worktree `postventa-f040`):
  merge de `dev` `ed9318e`, que trae F-072 `done` (en producción desde el
  2026-11-18) y lo integrado durante el aparcamiento. Anotada por el líder en T8.

## T8 · líder, 2026-11-19

- El humano aprueba la spec puesta al día y D-1..D-8 con la opción recomendada
  («lo recomendado», 2026-11-19). Escritas en la columna «Decidido» de
  `design.md` §12.
- D-8 aplicada: `impl_F-040.md` → `impl_F-040_hasta_2026-11-05.md` y
  `review_F-040.md` → `review_F-040_bloque1.md`; este informe y
  `progress/review_F-040.md` son los nuevos.
- F-040 pasa de `blocked` a `in_progress`.

## Bloque 1 bis · implementer, 2026-11-19 (T9–T11)

Alcance: solo `services/postventa-front`, su README y `docs/ARCHITECTURE.md`. Nada contra Sigrid ni producción;
datos de test ficticios (obra 9901, tipos `0002`/`0003` con etiquetas «…EJEMPLO», `9001` desconocido).

### T9 · RED

Tests nuevos: `tests_js/f040_tipo.test.js` (R63–R67, 20 casos) y, en `tests/test_f040_front.py`, R68 (miga actual
como `span`, con 3 controles), R67 (rótulo y sin `option value=""`; `opciones().listados` de `opcionesDeListado`),
R64 (`volcadoPorTipo()` en el resumen del ensayo) y R58/R63 (README y ARCHITECTURE con el tipo y sin «sin publicar
todavía»). Aserciones de F-038/F-040 que cambian, cada una con su R citado en el propio test:

| Test | Antes | Ahora | R |
|---|---|---|---|
| `revision.test.js` «f038 R4 (a)» | nueve motivos | diez, `tipo_fuera_de_sigrid` antes de `duplicada`, con su texto | R66 |
| `revision.test.js` «f038 R5» | título «nueve motivos» | «diez» (la aserción ya sale de `MOTIVOS`) | R66 |
| `revision.test.js` `TEXTOS_DE_PARTE` | «…no existe en Sigrid» | el texto de D-1 | R65 |
| `volcado.test.js` `catalogo().listados` | `[]` | `0002` y `0003` con etiqueta | R63 |
| `volcado.test.js` «f040 R51 juntarEnsayos» | «0002 PRIMER LISTADO POSTVENTA» ×4 | la etiqueta del catálogo | R63 |
| `volcado.test.js` «sin nombre en el catálogo» | tipo `0003` → `0003` | `9001` → `9001` (0003 ya tiene etiqueta) | R63 |
| `test_f038_front.py` `MIGAS_DE_BANDEJA` | dos enlaces | solo el de la portada; el `span`, en `test_f040_front.py` | R68 |
| `test_f038_front.py` control «miga-a-otra-seccion» | estropeaba el enlace `./#/bandeja` | estropea el de `index.html` | R68 |

Comando y resultado (traza recortada; base `be97272` + los tests):

```
$ node --test services/postventa-front/tests_js/f040_tipo.test.js services/postventa-front/tests_js/revision.test.js services/postventa-front/tests_js/volcado.test.js
ℹ tests 394  ℹ pass 374  ℹ fail 20
✖ f040 R63: el tipo de cada parte del ensayo sale con su etiqueta de catalogo.listados
  AssertionError [ERR_ASSERTION]: Expected values to be strictly deep-equal:
  +   '0002 PRIMER LISTADO POSTVENTA',
✖ f040 R63: un tipo que no está en catalogo.listados … sale con su código tal cual
✖ f040 R63: la tabla fija TEXTO_TIPO (Q-1, «siempre 0002») ya no existe
  AssertionError [ERR_ASSERTION]: The input was expected to not match the regular expression /TEXTO_TIPO/.
✖ f040 R64: recuentoPorTipo … / juntarEnsayos cuenta por tipo … / con dos tipos, la confirmación …
✖ f040 R64: textoPorTipo … / el componente pasa el recuento por tipo …
  AssertionError [ERR_ASSERTION]: The input did not match the regular expression /; por tipo, 2 PRIMER LISTADO EJEMPLO \(0002\) y 1 POST VENTA EJEMPLO \(0003\)\. Escribe 3/.
✖ f040 R65: tipo_no_valido tiene el texto que dice qué hacer … / un rechazado por tipo_no_valido …
✖ f040 R66: diez motivos, con tipo_fuera_de_sigrid entre proveedor_ambiguo y duplicada, y su texto
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:  9 !== 10
✖ f040 R66: el resumen cuenta diez motivos …
✖ f040 R67: opcionesDeListado con el tipo actual vigente …
  TypeError: Revision.opcionesDeListado is not a function
✖ f040 R67: … con un tipo de baja … / el formulario … / en el detalle y el historial … nunca «sin listado»
  AssertionError [ERR_ASSERTION]: The input was expected to not match the regular expression /sin listado/.
✖ f038 R4 (a) [F-040 R66]: los diez motivos …   ✖ f038 R21.4: … quince códigos de parte (tipo_no_valido)
✖ f040 R51: juntarEnsayos hace una tabla con los nombres del catálogo, el tipo …
✖ f038 T5 (BN12): control … ← AJENO: ver «Finales de línea» abajo; ya rojo en be97272 sin tocar nada
✔ f040 R64: con un solo tipo, el texto de la confirmación no cambia   ← guarda de no-regresión: pasa antes y después

$ python -m pytest services/postventa-front/tests -q
FAILED test_f038_front.py::test_f038_r1_migas_de_su_seccion_y_sin_subnavegacion
  AssertionError: bandeja.html: migas [('index.html', 'Portal de posventa'), ('./#/bandeja', 'Bandeja de revisión')], no [('index.html', 'Portal de posventa')]
FAILED test_f040_front.py::test_f040_r68_la_miga_actual_es_texto_sin_enlace            assert ['las migas e..., sin enlace'] == []
FAILED test_f040_front.py::test_f040_r68_control_una_miga_actual_mal_salta[×3]         el control ya no encuentra una sola vez: '<span aria-current="page">…'
FAILED test_f040_front.py::test_f040_r67_el_campo_listado_se_rotula_tipo_de_reclamacion_y_sin_opcion_en_blanco
  AssertionError: assert 'Listado' == 'Listado (tipo de reclamación)'
FAILED test_f040_front.py::test_f040_r67_opciones_listados_sale_de_opciones_de_listado
FAILED test_f040_front.py::test_f040_r64_el_resumen_del_ensayo_dice_el_recuento_por_tipo
FAILED test_f040_front.py::test_f040_r58_r63_la_documentacion_cuenta_el_tipo_y_ya_no_dice_sin_publicar[readme-r63, architecture-r63]
FAILED test_f007_js.py::test_f007_r32_la_suite_de_javascript_esta_en_verde   (la suite JS de arriba)
11 failed, 909 passed, 7 skipped
```

**Finales de línea (ajeno, ya en rojo en `be97272`).** `git ls-files --eol` da `w/crlf` en 18 ficheros del front
de este worktree (`core.autocrlf=true`), `bandeja.html` entre ellos; el índice está en LF. El control BN12 de F-038
(`revision.test.js`) busca `'@click="cancelarFormulario()"\n'` y con CRLF no lo encuentra: falla en la base sin
tocar nada (`node --test "tests_js/*.test.js"`: 1131/1132, solo BN12). No se cambian los finales de línea (encargo);
la verificación en LF va en T10, sobre una copia limpia del commit.

### T10 · GREEN (`288ee16`)

| Fichero | Qué |
|---|---|
| `js/volcado.js` | Fuera `TEXTO_TIPO`. `nombreDeTipo` (privada): etiqueta de `catalogo.listados`, si no el código, sin código `""`. La fila del ensayo lleva `tipo` (etiqueta) y `tipo_codigo`. Nuevas `recuentoPorTipo(filas, catalogo)` y `textoPorTipo(porTipo)` (vacío con < 2 tipos); `juntarEnsayos` da `porTipo` (solo `previsto`); `textoConfirmacion(n, porUnidad, obra, porTipo)` añade «; por tipo, …» solo con > 1; método `volcadoPorTipo()` |
| `js/revision.js` | `MOTIVOS` 10 (`tipo_fuera_de_sigrid` entre `proveedor_ambiguo` y `duplicada`) y su texto D-1; `tipo_no_valido` con el texto de R65; `textoDeCampo("listado")` = etiqueta o código (nunca «sin listado»); nueva `opcionesDeListado(catalogo, actual)`, usada por `opciones().listados` con `f.vigentes.listado` |
| `bandeja.html` | Miga actual `<span aria-current="page">`; campo «Listado (tipo de reclamación)» sin `<option value="">`; `<p x-show/x-text="volcadoPorTipo()">` en el resumen del ensayo |
| `README.md` del front, `docs/ARCHITECTURE.md` | Sección del panel: publicado el 2026-11-02 (fuera «sin publicar todavía») y el tipo de reclamación (R63, R64, R65; en ARCHITECTURE también R66/R67) |

Decisiones (dentro de la spec, para el reviewer):
- **Literal de R64**: confirmación «…: 2 de VILLA 91 y 1 de VILLA 92; por tipo, 2 <etiqueta> y 1 <etiqueta>. Escribe 3
  para confirmar.»; resumen «Por tipo: 2 <etiqueta> y 1 <etiqueta>». El boceto de §2 («y n₁ …») daba una lista
  ambigua tras la de unidades; se separa con «; por tipo,». El formato de la etiqueta es el de `catalogo.listados`.
- **R67, «actual»** = el tipo guardado (`formulario.vigentes.listado`): la opción del no vigente sigue aunque se elija otro
  en el desplegable, para poder volver a él sin recargar. Su forma `{codigo, etiqueta, fueraDeLista}` (el HTML usa
  `codigo` y `etiqueta`, como antes).
- **Listado nulo en el detalle** (no debería llegar: el backend no devuelve nulo): sale vacío, no «sin listado» ni un
  `0002` inferido.
- **Finales de línea**: los ficheros CRLF del worktree se editaron conservando CRLF (comprobado: nº de `\r\n` = nº de
  `\n` en `bandeja.html`, README y ARCHITECTURE); los LF siguen en LF. El índice sigue en LF.

Verificación (comandos del encargo; `node --test services/postventa-front/tests_js` con un directorio no funciona en
Node v24.14.1 de este equipo —«test at services\postventa-front\tests_js:1:1 … test failed», también en la base—, así
que se usa el patrón de `test_f007_js.py`, `node --test "tests_js/*.test.js"`):

```
# worktree postventa-f040 (front en CRLF), tras T11
$ node --test "tests_js/*.test.js"                     ℹ tests 1151  ℹ pass 1150  ℹ fail 1   ✖ f038 T5 (BN12) ← ajeno (CRLF)
$ python -m pytest services/postventa-front/tests tests/test_f035_placeholders_vivos.py -q
FAILED test_f007_js.py::test_f007_r32_la_suite_de_javascript_esta_en_verde   (el mismo BN12)   1 failed, 938 passed, 7 skipped

# copia limpia de 288ee16 en LF (git -c core.autocrlf=false worktree add --detach, en el scratchpad)
$ node --test "tests_js/*.test.js"                     ℹ tests 1149  ℹ pass 1149  ℹ fail 0
$ python -m pytest … (con dev_front.ps1 en CRLF, como pide su test F-007 R36)   939 passed, 7 skipped
```

O sea: con el front en LF y `dev_front.ps1` en CRLF (lo que el encargo da por hecho) todo está en verde; el único rojo
del worktree es BN12, por el checkout en CRLF de `bandeja.html`, y no lo toca este bloque.

### T11 · Mutación (`progress/mutacion_F-040_bloque1bis.md`)

50 mutantes en 5 familias (A etiqueta del tipo y respaldo 10, B recuento por tipo con uno y dos tipos 16, C orden de los
motivos y textos 5, D opción del no vigente, rótulo e historial 13, E migas 5), en la copia LF (BN12 taparía al
asesino en el worktree). Primera pasada 46/50; **vivos A5–A8** (envio sin `tipo`, `listados` que no es lista, sin
`envio`): huecos reales, cerrados con dos tests «(T11)» en `tests_js/f040_tipo.test.js`; segunda pasada 4/4.
**50/50 muertos; ningún superviviente ni equivalente pendiente de aceptación.** Cada mutante se restauró byte a byte;
`git status` del worktree limpio de mutantes; la copia, retirada (`git worktree remove`).

### `bash harness/init.sh`: NO EJECUTADO

El líder avisó durante el encargo de que el venv del API (`services/postventa-api/.venv`) está vacío y pidió no
ejecutar `init.sh` ni el pytest del API hasta que avise de que está reconstruido. Ese aviso no ha llegado; el pytest
del front corre con el `.venv` de la raíz del repositorio principal (no depende del del API). **Pendiente**: lanzar
`bash harness/init.sh` en este worktree cuando el venv esté; cabe esperar en rojo el BN12 (CRLF, ajeno).

### Evidencias (Bloque 1 bis)

| Evidencia | Valor |
|---|---|
| Tests JS | 1151 (antes 1132: +19 de `f040_tipo.test.js`); worktree 1150/1151 (BN12 ajeno); copia LF 1149/1149 en `288ee16` (sin los 2 de T11) |
| Tests pytest del front + `test_f035_placeholders_vivos` | 939 + 7 skipped; worktree 938 + 1 rojo (el de la suite JS) |
| Cobertura de líneas cambiadas | N/A: no hay `.py` de producción (la puerta mide Python); rigor crítico cubierto con mutación |
| Mutantes | 50 generados, 50 muertos, 0 supervivientes, 0 equivalentes |
| Tiempo de la suite | JS ~6 s; pytest del front ~19 s |
| Capa e2e | Sin requisitos `(capa: e2e)` en R63–R68 (todos `unit`) |
| Documento del ecosistema | No en este bloque (R58 de `azure-apps` es T6 bis) |

### Pendiente

- `init.sh` (arriba). Review del Bloque 1 bis. T12 (merge y publicación, humano). La fila de prueba de T5.4 a `0003` (D-6)
  es del humano.
- Fuera de alcance tocado: ninguno. `services/postventa-api/` sin tocar. Nada contra Sigrid ni producción.

## T12 · publicación (humano) y comprobación (líder), 2026-11-21

- Merge del Bloque 1 bis a `dev` (`87e124e`, líder) junto con los arreglos de `Ajustes` y del proveedor;
  `ARNES_SIN_CACHE=1 bash harness/init.sh` en verde sobre `dev` `8ac908d` (2201 / 10382 / 920 passed).
- El humano publica backend y front desde una copia limpia de `dev`; `27_ventana_volcado.ps1` sin parámetros:
  **cerrada**.
- Comprobación del líder por el front, con la sesión del humano, solo lecturas: `GET /api/health` 200;
  `js/volcado.js` publicado sin `TEXTO_TIPO` y con `nombreDeTipo` y el recuento por tipo; `js/revision.js` con
  «Listado (tipo de reclamación)», los textos de D-1 y `tipo_fuera_de_sigrid`, sin «Sin listado»; la miga de
  `bandeja.html` con la página actual como `span`. `GET /api/revision` de la 0626 (200, 19,5 s) y la 0677
  (200, 14,7 s): 4 listados; 25 y 38 pares, ninguno con espacio final ni vacío (el arreglo del proveedor,
  publicado). Application Insights, 3 h: 0 excepciones, ninguna traza de aviso o superior, todas las
  peticiones 200.
- Siguiente: T5.3 (humano, 0626, ventana cerrada).

## T5.3 · confirmar con la ventana cerrada (líder, por encargo del humano), 2026-11-23

- El humano encarga al líder hacer las pruebas («haz tú las pruebas»); el clic de confirmar lo da el líder con la
  sesión del humano. Antes del clic, `VOLCADO_HABILITADO=false` leído en la Function (dos veces).
- Foto `28_` de la 0626, ANTES: 2 partes `PVI-` (`RS26.09/0439` SAT, `RS26.10/0074` NPR); MAX(cod) del mes
  `RS26.11/0083`. PASA.
- «Registrar»: una lectura de `revision/sigrid` (200); la fila «PRUEBA F-040 - ANULAR» sale en **choca** con
  `RS26.09/0439`. Con su casilla, `volcado/ensayo` 200: «Se crearía 1», columna Tipo «PRIMER LISTADO POSTVENTA
  (0002)» (R63, etiqueta y código).
- «Volcar 1 partes»: la confirmación dice «Se va a crear 1 parte en el ERP de producción de la obra 0626: 1 de
  <unidad>. Escribe 1 para confirmar.» Con el 1: **una** petición `POST volcado/volcar`, **503**; en Application
  Insights, `volcado/volcar no procede: volcado_deshabilitado (503)`. El panel dice «La ventana del volcado está
  cerrada. No se ha escrito nada.» y el resultado «Creados 0 · Sin volcar 1». Ningún reintento; después, solo
  la recarga de la bandeja.
- Foto `28_` DESPUÉS: idéntica (2 partes `PVI-`, MAX(cod) `RS26.11/0083`). PASA.
- Siguiente: T5.4, la única escritura real, con la autorización expresa del humano en el chat (R69).
