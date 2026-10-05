// services/postventa-front/tests_js/f035_paginas.test.js
// F-035 · Enmienda del 2026-10-05: el portal en producción tras F-036, en lógica.
//
// Lo de la enmienda (`requirements.md` §1.12, `design.md` §16) que se prueba
// con `node --test`: `js/portal.js` cargado de verdad, y las barras leídas
// como texto y cruzadas con sus catálogos.
//
// Bloque 8 (`tasks.md`, T25):
//
// - **R62**: `Portal.enConstruccion(id)`, que sale del `estado` de cada
//   entrada de `Portal.SECCIONES` (el estado frente a `features.json` lo
//   vigila la raíz, `tests/test_f035_placeholders_vivos.py`).
// - **R66**: en la barra de `index.html` y en la de `partes.html`, la pestaña
//   de cada sección en `construccion` lleva `data-construccion` y
//   `aria-label="<etiqueta> (en construcción)"`, y ninguna otra los lleva.
//   Las barras de `importar.html` y `oficios.html` entran en los bloques 10 y
//   11 (`PAGINAS_CON_BARRA` crece entonces).
//
// Bloque 9 (`tasks.md`, T27):
//
// - **R65**: `Portal.fichasDeSeccion(id)`, las fichas que nombra el rótulo de
//   un recuadro de sección, y lo que el componente le da al rótulo
//   (`fichasDeSeccion`, `titulos`).
// - **R67**: fuera los contadores de la portada, y ningún texto que pinta el
//   portal (catálogo de placeholders, su aviso —también el genérico—, los
//   títulos de las fichas y los datos de ejemplo) dice «maqueta».
//
// El módulo se carga DENTRO de cada test, como en `portal.test.js`: en la
// fase RED un `require` de cabecera tumbaría el fichero entero sin nombre de
// requisito.

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const RAIZ_FRONT = path.resolve(__dirname, "..");

function portal() {
  return require("../js/portal.js");
}

function leer(relativa) {
  return fs.readFileSync(path.join(RAIZ_FRONT, relativa), "utf8");
}

/** Las páginas que llevan hoy la barra superior común (R66). */
const PAGINAS_CON_BARRA = ["index.html", "partes.html"];

const ESTADOS_DE_SECCION = ["real", "parcial", "construccion"];

// ── Las pestañas de una barra, leídas del HTML ──────────────────────────────
//
// Basta un lector acotado: la barra es HTML estático (R45 en el circuito) y
// sus pestañas son `<a>` o `<span>` con la clase `rs-pestana`, sin hijos.
// Los atributos se leen respetando las comillas (en Alpine llevan `'`).

const ATRIBUTO = /([^\s"'=<>\/]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+)))?/g;
const ETIQUETA = /<(a|span)((?:\s+[^\s"'=<>\/]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'>]+))?)*)\s*>([^<]*)<\/\1>/g;

function atributosDe(trozo) {
  const atributos = {};
  for (const m of trozo.matchAll(ATRIBUTO)) {
    atributos[m[1]] = m[2] ?? m[3] ?? m[4] ?? "";
  }
  return atributos;
}

/** `[{nombre, atributos, texto}]` de las pestañas `rs-pestana` de la barra de ese HTML. */
function pestanasDeLaBarra(html) {
  const sinComentarios = html.replace(/<!--[\s\S]*?-->/g, "");
  const inicio = sinComentarios.search(/<nav\b[^>]*\bdata-barra-portal\b/);
  assert.notEqual(inicio, -1, "no hay <nav data-barra-portal>");
  const fin = sinComentarios.indexOf("</nav>", inicio);
  const barra = sinComentarios.slice(inicio, fin);
  const pestanas = [];
  for (const m of barra.matchAll(ETIQUETA)) {
    const atributos = atributosDe(m[2]);
    if ((atributos.class || "").split(/\s+/).includes("rs-pestana")) {
      pestanas.push({ nombre: m[1], atributos, texto: m[3].replace(/\s+/g, " ").trim() });
    }
  }
  return pestanas;
}

/**
 * Lo que la barra de ese HTML incumple de R66: lista vacía = correcto.
 * Cada sección de `Portal.SECCIONES` tiene que tener su pestaña; las que
 * están en `construccion` llevan `data-construccion` y su `aria-label`, y
 * ninguna otra lleva ninguno de los dos.
 */
function problemasR66(html, Portal) {
  const pestanas = pestanasDeLaBarra(html);
  const problemas = [];
  for (const seccion of Portal.SECCIONES) {
    const pestana = pestanas.find((p) => p.texto === seccion.etiqueta);
    if (!pestana) {
      problemas.push(`falta la pestaña «${seccion.etiqueta}»`);
      continue;
    }
    const marcada = "data-construccion" in pestana.atributos;
    const etiquetaAccesible = pestana.atributos["aria-label"];
    if (Portal.enConstruccion(seccion.id)) {
      if (!marcada) problemas.push(`«${seccion.etiqueta}» está en construcción y no lleva data-construccion`);
      if (etiquetaAccesible !== `${seccion.etiqueta} (en construcción)`) {
        problemas.push(`«${seccion.etiqueta}»: aria-label «${etiquetaAccesible}», no «${seccion.etiqueta} (en construcción)»`);
      }
    } else {
      if (marcada) problemas.push(`«${seccion.etiqueta}» no está en construcción y lleva data-construccion`);
      if (etiquetaAccesible !== undefined) problemas.push(`«${seccion.etiqueta}» no está en construcción y lleva aria-label`);
    }
  }
  return problemas;
}

// ── R62 · El estado de cada sección y `enConstruccion` ──────────────────────

test("f035 R62: cada entrada de SECCIONES declara un estado válido", () => {
  const { SECCIONES } = portal();

  for (const seccion of SECCIONES) {
    assert.ok(
      ESTADOS_DE_SECCION.includes(seccion.estado),
      `«${seccion.id}» declara estado «${seccion.estado}»; solo ${ESTADOS_DE_SECCION.join(", ")}`,
    );
  }
});

test("f035 R62: enConstruccion es true justo para las secciones en construccion", () => {
  const { SECCIONES, enConstruccion } = portal();

  for (const seccion of SECCIONES) {
    assert.equal(enConstruccion(seccion.id), seccion.estado === "construccion", `enConstruccion("${seccion.id}")`);
  }
  assert.ok(SECCIONES.some((s) => enConstruccion(s.id)), "hoy hay secciones en construcción (R62)");
  assert.ok(SECCIONES.some((s) => !enConstruccion(s.id)), "hoy hay secciones que funcionan (R62)");
});

test("f035 R62: enConstruccion con un id desconocido o vacío devuelve false y no lanza", () => {
  const { enConstruccion } = portal();

  for (const raro of ["no-existe", "", undefined, null, 42, "BANDEJA"]) {
    assert.equal(enConstruccion(raro), false, `enConstruccion(${JSON.stringify(raro)})`);
  }
});

/**
 * `js/portal.js` con el `estado` de algunas secciones cambiado, cargado en un
 * contexto aparte (`node:vm`): sin tocar el fichero ni la caché de `require`.
 * Sirve para probar `enConstruccion` con estados que hoy no hay (`real`).
 */
function portalConEstados(cambios) {
  let fuente = leer("js/portal.js");
  for (const [id, estado] of Object.entries(cambios)) {
    const patron = new RegExp(`(\\{ id: "${id}",[^}]*?estado: ")[a-z]+(")`);
    assert.match(fuente, patron, `no se encuentra el estado de «${id}» en js/portal.js`);
    fuente = fuente.replace(patron, `$1${estado}$2`);
  }
  const modulo = { exports: {} };
  vm.runInNewContext(fuente, { module: modulo });
  return modulo.exports;
}

test("f035 R62: enConstruccion sigue al estado: real y parcial no, construccion sí", () => {
  // Mutación manual B8 del bloque 8: `estado !== "parcial"` sobrevivía porque
  // hoy ninguna sección es `real`.
  const Portal = portalConEstados({ entrada: "real", bandeja: "parcial", inicio: "construccion" });

  assert.equal(Portal.enConstruccion("entrada"), false, "una sección real no está en construcción");
  assert.equal(Portal.enConstruccion("bandeja"), false, "una sección parcial no está en construcción");
  assert.equal(Portal.enConstruccion("inicio"), true, "una sección en construccion sí");
  assert.equal(Portal.enConstruccion("datos"), true, "las demás, como estaban");
});

test("f035 R62: inicio y partes nunca están en construcción", () => {
  const { enConstruccion } = portal();

  assert.equal(enConstruccion("inicio"), false, "inicio es la portada: parcial o real");
  assert.equal(enConstruccion("partes"), false, "partes es el circuito, que funciona");
});

// ── R66 · Las pestañas en construcción, marcadas en las barras ──────────────

for (const pagina of PAGINAS_CON_BARRA) {
  test(`f035 R66: en la barra de ${pagina}, data-construccion y aria-label solo en las secciones en construcción`, () => {
    const Portal = portal();

    assert.deepEqual(problemasR66(leer(pagina), Portal), []);
  });
}

test("f035 R66: control: el lector ve las ocho pestañas de cada barra, en su orden", () => {
  const { SECCIONES } = portal();

  for (const pagina of PAGINAS_CON_BARRA) {
    assert.deepEqual(
      pestanasDeLaBarra(leer(pagina)).map((p) => p.texto),
      SECCIONES.map((s) => s.etiqueta),
      `${pagina}: pestañas leídas`,
    );
  }
});

test("f035 R66: control: quitar data-construccion de una pestaña de partes.html salta", () => {
  const Portal = portal();
  const html = leer("partes.html");
  const estropeado = html.replace(/(<a\b[^>]*href="\.\/#\/bandeja"[^>]*?)\s+data-construccion\b/, "$1");

  assert.notEqual(estropeado, html, "el control no encuentra data-construccion en la pestaña de bandeja");
  const problemas = problemasR66(estropeado, Portal);
  assert.equal(problemas.length, 1, problemas.join("\n"));
  assert.match(problemas[0], /Bandeja de revisión.*data-construccion/);
});

test("f035 R66: control: marcar una pestaña que funciona, o cambiar su aria-label, salta", () => {
  const Portal = portal();
  const html = leer("index.html");

  const entradaMarcada = html.replace(/<a href="#\/entrada"/, '<a href="#/entrada" data-construccion');
  assert.notEqual(entradaMarcada, html, "el control no encuentra la pestaña de entrada");
  assert.ok(
    problemasR66(entradaMarcada, Portal).some((p) => p.startsWith("«Entrada» no está en construcción")),
    "una pestaña que funciona, marcada, tiene que saltar",
  );

  const otraEtiqueta = html.replace('aria-label="Coste y venta (en construcción)"', 'aria-label="Coste y venta"');
  assert.notEqual(otraEtiqueta, html, "el control no encuentra el aria-label de Coste y venta");
  assert.ok(
    problemasR66(otraEtiqueta, Portal).some((p) => p.startsWith("«Coste y venta»: aria-label")),
    "un aria-label sin «(en construcción)» tiene que saltar",
  );
});

// ── Bloque 9 · El rótulo «En construcción» (R65) y la portada (R67) ─────────
//
// `Portal.fichasDeSeccion(id)` (`design.md` §16.8) da al rótulo de cada
// recuadro de sección la lista «La construirán: F-0NN · <título>». Salen de
// `TITULOS_FICHAS`, que guarda solo las fichas por construir (la que se
// cierra borra su título, `design.md` §7.3): por eso una ficha de la sección
// sin título —F-036 en `entrada`, ya `done`— no se lista.

/** El componente del portal con un `window` mínimo, sin red ni hash. */
function componente() {
  const previo = global.window;
  global.window = {
    Portal: portal(),
    MaquetaDatos: require("../js/maqueta_datos.js"),
    location: { hash: "" },
    addEventListener() {},
  };
  try {
    return require("../js/portal_app.js")();
  } finally {
    if (previo === undefined) delete global.window;
    else global.window = previo;
  }
}

test("f035 R65: fichasDeSeccion da cada ficha de la sección con su título, en su orden", () => {
  const { fichasDeSeccion, TITULOS_FICHAS } = portal();

  assert.deepEqual(fichasDeSeccion("bandeja"), [
    { ficha: "F-038", titulo: TITULOS_FICHAS["F-038"] },
    { ficha: "F-039", titulo: TITULOS_FICHAS["F-039"] },
    { ficha: "F-040", titulo: TITULOS_FICHAS["F-040"] },
    { ficha: "F-043", titulo: TITULOS_FICHAS["F-043"] },
  ]);
  assert.deepEqual(fichasDeSeccion("impresion"), [{ ficha: "F-044", titulo: TITULOS_FICHAS["F-044"] }]);
  assert.equal(
    fichasDeSeccion("datos")[0].titulo,
    "Los datos de posventa al datamart",
    "el título es el de features.json, copiado en TITULOS_FICHAS",
  );
});

test("f035 R65: fichasDeSeccion no lista una ficha ya hecha (sin título en TITULOS_FICHAS)", () => {
  const { fichasDeSeccion } = portal();

  assert.deepEqual(
    fichasDeSeccion("entrada").map((f) => f.ficha),
    ["F-037"],
    "F-036 está done: importar y oficios funcionan y no «la construirán»",
  );
  assert.deepEqual(fichasDeSeccion("inicio"), [], "inicio no tiene fichas propias");
});

test("f035 R65: cada sección en construcción tiene al menos una ficha que nombrar", () => {
  const { SECCIONES, fichasDeSeccion } = portal();

  for (const seccion of SECCIONES.filter((s) => s.estado === "construccion")) {
    const fichas = fichasDeSeccion(seccion.id);
    assert.ok(fichas.length > 0, `«${seccion.id}» está en construcción y su rótulo no nombraría ninguna ficha`);
    assert.deepEqual(
      fichas.map((f) => f.ficha),
      seccion.fichas,
      `«${seccion.id}»: todas sus fichas, en su orden`,
    );
    for (const f of fichas) assert.ok(f.titulo && f.titulo.trim(), `${f.ficha} sin título`);
  }
});

test("f035 R65: fichasDeSeccion con un id desconocido o raro devuelve [] y no lanza", () => {
  const { fichasDeSeccion } = portal();

  for (const raro of ["no-existe", "", undefined, null, 42, "BANDEJA"]) {
    assert.deepEqual(fichasDeSeccion(raro), [], `fichasDeSeccion(${JSON.stringify(raro)})`);
  }
});

test("f035 R65: fichasDeSeccion devuelve una lista nueva cada vez (el rótulo no puede tocar el catálogo)", () => {
  const { fichasDeSeccion, SECCIONES } = portal();

  const una = fichasDeSeccion("economico");
  una.push({ ficha: "F-999", titulo: "x" });
  assert.deepEqual(fichasDeSeccion("economico").map((f) => f.ficha), ["F-046", "F-047"]);
  assert.deepEqual(SECCIONES.find((s) => s.id === "economico").fichas, ["F-046", "F-047"]);
});

test("f035 R65: el componente da al rótulo fichasDeSeccion y los títulos, delegando en Portal", () => {
  const c = componente();
  const Portal = portal();

  assert.deepEqual(c.fichasDeSeccion("bandeja"), Portal.fichasDeSeccion("bandeja"));
  assert.deepEqual(c.fichasDeSeccion("no-existe"), []);
  assert.equal(c.titulos, Portal.TITULOS_FICHAS, "los recuadros de bloque leen titulos['F-0NN']");
  assert.equal(c.titulos["F-037"], Portal.TITULOS_FICHAS["F-037"]);
  assert.equal(c.titulos["F-045"], Portal.TITULOS_FICHAS["F-045"]);
});

test("f035 R67: la portada ya no tiene contadores: fuera contadoresInicio y contadores()", () => {
  const Portal = portal();
  const c = componente();

  assert.equal(Portal.contadoresInicio, undefined, "fuera Portal.contadoresInicio (design.md §16.5)");
  assert.equal(c.contadores, undefined, "fuera contadores() del componente");
});

/** Todos los textos (cadenas) de un valor, recorriendo objetos y listas. */
function textosDe(valor, ruta, lista) {
  if (typeof valor === "string") lista.push([ruta, valor]);
  else if (valor && typeof valor === "object") {
    for (const [k, v] of Object.entries(valor)) textosDe(v, `${ruta}.${k}`, lista);
  }
  return lista;
}

test("f035 R67: ningún texto que pinta el portal dice «maqueta»", () => {
  const Portal = portal();
  const datos = require("../js/maqueta_datos.js");

  const textos = [
    ...textosDe(Portal.PLACEHOLDERS, "PLACEHOLDERS", []),
    ...textosDe(Portal.TITULOS_FICHAS, "TITULOS_FICHAS", []),
    ...textosDe(datos, "MaquetaDatos", []),
    ...Portal.PLACEHOLDERS.map((p) => [`textoPlaceholder(${p.id})`, Portal.textoPlaceholder(p.id, { seleccionadas: 2 })]),
    ["textoPlaceholder (genérico)", Portal.textoPlaceholder("no.existe")],
    ["textoPlaceholder (sin id)", Portal.textoPlaceholder(undefined)],
  ];
  const conMaqueta = textos.filter(([, t]) => /maqueta/i.test(t));

  assert.ok(textos.length > 100, `el recorrido ve los textos (${textos.length})`);
  assert.deepEqual(conMaqueta, [], "en producción la palabra es «en construcción» (R67)");
});

test("f035 R67: el texto genérico de un placeholder desconocido dice que está en construcción", () => {
  const { textoPlaceholder } = portal();

  const aviso = textoPlaceholder("no.existe");
  assert.match(aviso, /^Todavía no hace nada/);
  assert.match(aviso, /en construcción/);
});
