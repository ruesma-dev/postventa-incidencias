<!-- progress/mutacion_F-040_bloque1bis.md -->
# F-040 · Bloque 1 bis · Mutación a mano por familias (T11)

Rigor `critico`. Lo cambiado en T10 (`288ee16`): `js/volcado.js`, `js/revision.js` y `bandeja.html`. Cada mutante
cambia UNA cadena (que ha de estar una sola vez), se ejecutan los tests y se restaura el fichero byte a byte.

- **Dónde**: en una copia limpia del commit con finales LF (`git -c core.autocrlf=false worktree add --detach`,
  en el scratchpad), porque en el worktree `postventa-f040` el control BN12 de F-038 está en rojo por CRLF (ajeno,
  ver `progress/impl_F-040.md`) y taparía qué test mata a cada mutante. En la copia la suite JS está 1149/1149.
- **Qué se ejecuta**: `node --test` sobre `f040_tipo`, `revision`, `volcado`, `f035_paginas`, `f040_enlace_bandeja`
  y `portal`; en los mutantes de `bandeja.html` y de `opciones()` (D8, D9), también `pytest` sobre `test_f040_front`,
  `test_f038_front`, `test_f035_paginas` y `test_f035_portal`. Muerto = alguno de los dos sale con código ≠ 0.
- **Primera pasada** (`288ee16`): 50 mutantes, 46 muertos, **4 vivos (A5–A8)**: bordes del tipo que ningún test
  fijaba (envio sin `tipo`, `listados` que no es lista, sin `envio`). Huecos reales, no equivalentes: cada uno cambia lo
  observable (A5 da `"undefined"` como tipo; A7, `tipo_codigo` `undefined`; A8, `""` en vez de `—`; A6 lanza `TypeError`
  con un `listados` que no es lista), y el test nuevo, en verde sobre `288ee16`, falla con cada uno.
  Cerrados con dos tests nuevos en `tests_js/f040_tipo.test.js` (« (T11)»); **segunda pasada: los 4, muertos**.
- **Resultado: 50 mutantes, 50 muertos, ningún superviviente ni equivalente.** Tras cada uno, el fichero se
  restauró; al final, `git status` limpio en la copia salvo el test nuevo copiado, y la copia se retiró.

## A · La etiqueta del tipo y su respaldo (R63)

| Mutante | Fichero | Antes | Después | Test asesino |
|---|---|---|---|---|
| A1 | `js/volcado.js` | `return (tipo && tipo.etiqueta) \|\| String(codigo);` | `return String(codigo);` | f040 R63: el tipo de cada parte del ensayo sale con su etiqueta de catalogo.listados |
| A2 | `js/volcado.js` | `return (tipo && tipo.etiqueta) \|\| String(codigo);` | `return tipo && tipo.etiqueta;` | f040 R63: un tipo que no está en catalogo.listados (de baja o desconocido) sale con su código tal cual |
| A3 | `js/volcado.js` | `return (tipo && tipo.etiqueta) \|\| String(codigo);` | `return (tipo && tipo.etiqueta) \|\| "";` | f040 R63: un tipo que no está en catalogo.listados (de baja o desconocido) sale con su código tal cual |
| A4 | `js/volcado.js` | `return l && l.codigo === codigo;` | `return l && l.codigo !== codigo;` | f040 R63: el tipo de cada parte del ensayo sale con su etiqueta de catalogo.listados |
| A5 (2.ª pasada) | `js/volcado.js` | `if (codigo === null \|\| codigo === undefined \|\| codigo === "") { ⏎ return ""; ⏎ } ⏎ con…` | `const listados` | f040 R63 (T11): un envio sin tipo da tipo vacío y tipo_codigo null; sin envio, el guion |
| A6 (2.ª pasada) | `js/volcado.js` | `const listados = (catalogo && Array.isArray(catalogo.listados) && catalogo.listados) \|\| …` | `const listados = (catalogo && catalogo.listados) \|\| [];` | f040 R63 (T11): un catalogo.listados que no es una lista no rompe: el código tal cual |
| A7 (2.ª pasada) | `js/volcado.js` | `tipo_codigo: envio && envio.tipo ? envio.tipo : null,` | `tipo_codigo: envio ? envio.tipo : null,` | f040 R63 (T11): un envio sin tipo da tipo vacío y tipo_codigo null; sin envio, el guion |
| A8 (2.ª pasada) | `js/volcado.js` | `tipo: envio ? nombreDeTipo(catalogo, envio.tipo) : SIN_DATO,` | `tipo: nombreDeTipo(catalogo, envio && envio.tipo),` | f040 R63 (T11): un envio sin tipo da tipo vacío y tipo_codigo null; sin envio, el guion |
| A9 | `js/volcado.js` | `tipo: envio ? nombreDeTipo(catalogo, envio.tipo) : SIN_DATO,` | `tipo: envio ? envio.tipo : SIN_DATO,` | f040 R63: el tipo de cada parte del ensayo sale con su etiqueta de catalogo.listados |
| A10 | `js/volcado.js` | `tipo: envio ? nombreDeTipo(catalogo, envio.tipo) : SIN_DATO,` | `tipo: envio ? nombreDeTipo(null, envio.tipo) : SIN_DATO,` | f040 R63: el tipo de cada parte del ensayo sale con su etiqueta de catalogo.listados |

## B · El recuento por tipo, con uno y dos tipos (R64)

| Mutante | Fichero | Antes | Después | Test asesino |
|---|---|---|---|---|
| B1 | `js/volcado.js` | `porTipo: recuentoPorTipo(previstas, catalogo),` | `porTipo: recuentoPorTipo(filas, catalogo),` | f040 R64: juntarEnsayos cuenta por tipo solo lo que se crearía (los previsto) |
| B2 | `js/volcado.js` | `porTipo: recuentoPorTipo(previstas, catalogo),` | `porTipo: [],` | f040 R64: juntarEnsayos cuenta por tipo solo lo que se crearía (los previsto) |
| B3 | `js/volcado.js` | `cuentas[indice[codigo]].n += 1; ⏎ }); ⏎ return cuentas; ⏎ } ⏎  ⏎ /** R64 [D-2] · el recuen…` | `cuentas[indice[codigo]].n = 1; ⏎ }); ⏎ return cuentas; ⏎ } ⏎  ⏎ /** R64 [D-2] · el recuent…` | f040 R64: recuentoPorTipo cuenta por tipo, en el orden de aparición, con su etiqueta (o el código) |
| B4 | `js/volcado.js` | `const codigo = fila.tipo_codigo; ⏎ if (!propio(indice, codigo)) {` | `const codigo = fila.tipo_codigo; ⏎ if (true) {` | f040 R64: recuentoPorTipo cuenta por tipo, en el orden de aparición, con su etiqueta (o el código) |
| B5 | `js/volcado.js` | `cuentas.push({ tipo_codigo: codigo, etiqueta: nombreDeTipo(catalogo, codigo), n: 0 });` | `cuentas.push({ tipo_codigo: codigo, etiqueta: codigo, n: 0 });` | f040 R64: recuentoPorTipo cuenta por tipo, en el orden de aparición, con su etiqueta (o el código) |
| B6 | `js/volcado.js` | `if (tipos.length < 2) { ⏎ return "";` | `if (tipos.length < 1) { ⏎ return "";` | f040 R64: textoPorTipo (el resumen del ensayo) es vacío con un tipo o ninguno y dice el recuento con dos o más |
| B7 | `js/volcado.js` | `if (tipos.length < 2) { ⏎ return "";` | `if (tipos.length < 3) { ⏎ return "";` | f040 R64: el componente pasa el recuento por tipo a la confirmación y al resumen del ensayo |
| B8 | `js/volcado.js` | `tipos.length > 1` | `tipos.length > 0` | f040 R64: con un solo tipo, el texto de la confirmación no cambia |
| B9 | `js/volcado.js` | `tipos.length > 1` | `tipos.length > 2` | f040 R64: con dos tipos, la confirmación dice además el recuento por tipo con su etiqueta |
| B10 | `js/volcado.js` | `"; por tipo, " + listaConY` | `", y " + listaConY` | f040 R64: con dos tipos, la confirmación dice además el recuento por tipo con su etiqueta |
| B11 | `js/volcado.js` | `return t.n + " " + t.etiqueta; ⏎ })) ⏎ : "";` | `return t.n + " " + t.tipo_codigo; ⏎ })) ⏎ : "";` | f040 R64: con dos tipos, la confirmación dice además el recuento por tipo con su etiqueta |
| B12 | `js/volcado.js` | `"Por tipo: " + listaConY` | `"" + listaConY` | f040 R64: textoPorTipo (el resumen del ensayo) es vacío con un tipo o ninguno y dice el recuento con dos o más |
| B13 | `js/volcado.js` | `textoConfirmacion(vista.n, vista.porUnidad, this.volcado.obra, vista.porTipo)` | `textoConfirmacion(vista.n, vista.porUnidad, this.volcado.obra)` | f040 R64: el componente pasa el recuento por tipo a la confirmación y al resumen del ensayo |
| B14 | `js/volcado.js` | `return vista ? textoPorTipo(vista.porTipo) : "";` | `return textoPorTipo(vista && vista.porTipo).toUpperCase();` | f040 R64: el componente pasa el recuento por tipo a la confirmación y al resumen del ensayo |
| B15 | `bandeja.html` | `<p x-show="volcadoPorTipo()" class="mt-2 rs-nota" x-text="volcadoPorTipo()"></p>` | `<p class="mt-2 rs-nota" x-text="volcadoPorTipo()"></p>` | tests/test_f040_front.py::test_f040_r64_el_resumen_del_ensayo_dice_el_recuento_por_tipo |
| B16 | `bandeja.html` | `<p x-show="volcadoPorTipo()" class="mt-2 rs-nota" x-text="volcadoPorTipo()"></p>` | `(borrado)` | tests/test_f040_front.py::test_f040_r64_el_resumen_del_ensayo_dice_el_recuento_por_tipo |

## C · El orden de los motivos y los textos de Q-11 (R65, R66)

| Mutante | Fichero | Antes | Después | Test asesino |
|---|---|---|---|---|
| C1 | `js/revision.js` | `"tipo_fuera_de_sigrid", ⏎ "duplicada", ⏎ ];` | `"duplicada", ⏎ "tipo_fuera_de_sigrid", ⏎ ];` | f040 R66: diez motivos, con tipo_fuera_de_sigrid entre proveedor_ambiguo y duplicada, y su texto |
| C2 | `js/revision.js` | `"tipo_fuera_de_sigrid", ⏎ "duplicada", ⏎ ];` | `"duplicada", ⏎ ];` | f040 R66: diez motivos, con tipo_fuera_de_sigrid entre proveedor_ambiguo y duplicada, y su texto |
| C3 | `js/revision.js` | `"proveedor_ambiguo", ⏎ "tipo_fuera_de_sigrid",` | `"tipo_fuera_de_sigrid", ⏎ "proveedor_ambiguo",` | f040 R66: diez motivos, con tipo_fuera_de_sigrid entre proveedor_ambiguo y duplicada, y su texto |
| C4 | `js/revision.js` | `tipo_fuera_de_sigrid: "El tipo de reclamación ya no está vigente en Sigrid: elige otro",` | `tipo_fuera_de_sigrid: "El tipo de reclamación ya no está vigente en Sigrid",` | f040 R66: diez motivos, con tipo_fuera_de_sigrid entre proveedor_ambiguo y duplicada, y su texto |
| C5 | `js/revision.js` | `"El tipo de reclamación no existe o está de baja en Sigrid: cambia el tipo en la revisión …` | `"El tipo de reclamación no existe en Sigrid"` | f040 R65: tipo_no_valido tiene el texto que dice qué hacer, en TEXTO_MOTIVO_VOLCADO de revision.js |

## D · La opción del tipo no vigente, el rótulo y el historial (R67)

| Mutante | Fichero | Antes | Después | Test asesino |
|---|---|---|---|---|
| D1 | `js/revision.js` | `if (actual && !estaEn(opciones, actual)) {` | `if (!estaEn(opciones, actual)) {` | f040 R67: opcionesDeListado con el tipo actual vigente: los de catalogo.listados, sin opción en blanco |
| D2 | `js/revision.js` | `if (actual && !estaEn(opciones, actual)) {` | `if (actual && estaEn(opciones, actual)) {` | f040 R67: opcionesDeListado con el tipo actual vigente: los de catalogo.listados, sin opción en blanco |
| D3 | `js/revision.js` | `if (actual && !estaEn(opciones, actual)) {` | `if (false) {` | f040 R67: opcionesDeListado con un tipo de baja añade una opción más con su código y «(ya no vigente en Sigrid)» |
| D4 | `js/revision.js` | `etiqueta: actual + " (" + TEXTO_LISTADO_NO_VIGENTE + ")", fueraDeLista: true` | `etiqueta: actual, fueraDeLista: true` | f040 R67: opcionesDeListado con un tipo de baja añade una opción más con su código y «(ya no vigente en Sigrid)» |
| D5 | `js/revision.js` | `etiqueta: actual + " (" + TEXTO_LISTADO_NO_VIGENTE + ")", fueraDeLista: true` | `etiqueta: actual + " (" + TEXTO_LISTADO_NO_VIGENTE + ")", fueraDeLista: false` | f040 R67: opcionesDeListado con un tipo de baja añade una opción más con su código y «(ya no vigente en Sigrid)» |
| D6 | `js/revision.js` | `return { codigo: listado.codigo, etiqueta: listado.etiqueta, fueraDeLista: false };` | `return { codigo: listado.codigo, etiqueta: listado.codigo, fueraDeLista: false };` | f040 R67: opcionesDeListado con el tipo actual vigente: los de catalogo.listados, sin opción en blanco |
| D7 | `js/revision.js` | `const opciones = ((catalogo && catalogo.listados) \|\| []).map(function (listado) {` | `const opciones = [{ codigo: "", etiqueta: "Sin listado" }].concat((catalogo && catalogo.li…` | f040 R67: opcionesDeListado con el tipo actual vigente: los de catalogo.listados, sin opción en blanco |
| D8 | `js/revision.js` | `listados: opcionesDeListado(catalogo, f.vigentes.listado),` | `listados: opcionesDeListado(catalogo, f.listado),` | f040 R67: el formulario de la revisión ofrece opcionesDeListado del tipo de la incidencia |
| D9 | `js/revision.js` | `listados: opcionesDeListado(catalogo, f.vigentes.listado),` | `listados: catalogo.listados \|\| [],` | f040 R67: el formulario de la revisión ofrece opcionesDeListado del tipo de la incidencia |
| D10 | `js/revision.js` | `return etiquetaDe(cat.listados, v.listado);` | `return v.listado ? etiquetaDe(cat.listados, v.listado) : "sin listado";` | f040 R67: en el detalle y el historial, el listado sale con su etiqueta o su código, nunca «sin listado» |
| D11 | `js/revision.js` | `return etiquetaDe(cat.listados, v.listado);` | `return v.listado \|\| "";` | f040 R67: en el detalle y el historial, el listado sale con su etiqueta o su código, nunca «sin listado» |
| D12 | `bandeja.html` | `<span class="rs-campo__etiqueta">Listado (tipo de reclamación)</span>` | `<span class="rs-campo__etiqueta">Listado</span>` | tests/test_f040_front.py::test_f040_r67_el_campo_listado_se_rotula_tipo_de_reclamacion_y_sin_opcion_en_blanco |
| D13 | `bandeja.html` | `<select x-model="formulario.listado" class="rs-campo"> ⏎ <template` | `<select x-model="formulario.listado" class="rs-campo"> ⏎ <option value="">Sin listado</opt…` | tests/test_f040_front.py::test_f040_r67_el_campo_listado_se_rotula_tipo_de_reclamacion_y_sin_opcion_en_blanco |

## E · Las migas (R68)

| Mutante | Fichero | Antes | Después | Test asesino |
|---|---|---|---|---|
| E1 | `bandeja.html` | `<span aria-current="page">Bandeja de revisión</span>` | `<a href="./#/bandeja" class="rs-enlace">Bandeja de revisión</a>` | tests/test_f040_front.py::test_f040_r68_la_miga_actual_es_texto_sin_enlace |
| E2 | `bandeja.html` | `<span aria-current="page">Bandeja de revisión</span>` | `<span>Bandeja de revisión</span>` | tests/test_f040_front.py::test_f040_r68_la_miga_actual_es_texto_sin_enlace |
| E3 | `bandeja.html` | `<span aria-hidden="true">›</span> ⏎ <span aria-current="page">Bandeja de revisión</span>` | `(borrado)` | tests/test_f040_front.py::test_f040_r68_la_miga_actual_es_texto_sin_enlace |
| E4 | `bandeja.html` | `<span aria-current="page">Bandeja de revisión</span>` | `<a href="./#/bandeja" class="rs-enlace" aria-current="page">Bandeja de revisión</a>` | tests/test_f040_front.py::test_f040_r68_la_miga_actual_es_texto_sin_enlace |
| E5 | `bandeja.html` | `<span aria-current="page">Bandeja de revisión</span>` | `<span aria-current="step">Bandeja de revisión</span>` | tests/test_f040_front.py::test_f040_r68_la_miga_actual_es_texto_sin_enlace |
