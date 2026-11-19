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
