// services/postventa-front/tests_js/f040_enlace_bandeja.test.js
// F-040 · T6a (`specs/F-040-volcado-sigrid/tasks.md`): decisión del humano del
// 2026-11-04, adelantada de T6 sin esperar a F-038. La navegación del front que
// llevaba a la maqueta de la bandeja (`#/bandeja`) lleva a la página real,
// `bandeja.html`:
//
// - `Portal.enlaceSeccion("bandeja", desde)` da `bandeja.html` desde el portal,
//   el circuito y las páginas reales de otra sección; desde `bandeja.html`,
//   `null` (es la suya).
// - En las barras de `index.html`, `partes.html`, `importar.html` y
//   `oficios.html`, la pestaña «Bandeja de revisión» y los pasos «02 Revisión»
//   y «03 Sigrid» son `<a href="bandeja.html">`, sin `data-construccion`, sin
//   «(en construcción)» en su `aria-label` y sin `:aria-current` (la pestaña de
//   `partes.html` en el portal, que lleva a otra página, tampoco lo lleva).
// - La tarjeta «Bandeja de revisión» de la portada va a `bandeja.html`.
// - `Portal.marcadaEnConstruccion(id, desde)`: la marca de R66/R87 es para lo
//   que lleva a la maqueta; la pestaña actual de `bandeja.html` y sus pasos 02
//   y 03, que no enlazan, siguen la sección (R2 y R25 de F-038).
// - La ruta `#/bandeja` de la maqueta sigue existiendo.
//
// El módulo se carga DENTRO de cada test, como en `portal.test.js`.

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const RAIZ_FRONT = path.resolve(__dirname, "..");

function portal() {
  return require("../js/portal.js");
}

function leer(relativa) {
  return fs.readFileSync(path.join(RAIZ_FRONT, relativa), "utf8");
}

//: Las páginas que enlazan la sección `bandeja` y su `desde` de `enlaceSeccion`.
const PAGINAS_QUE_ENLAZAN_LA_BANDEJA = [
  ["index.html", "portal"],
  ["partes.html", "circuito"],
  ["importar.html", "importar.html"],
  ["oficios.html", "oficios.html"],
];

const ETIQUETA = /<(a|span)\b((?:\s+[^\s"'=<>\/]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'>]+))?)*)\s*>([\s\S]*?)<\/\1>/g;
const ATRIBUTO = /([^\s"'=<>\/]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+)))?/g;

function atributosDe(trozo) {
  const atributos = {};
  for (const m of trozo.matchAll(ATRIBUTO)) atributos[m[1]] = m[2] ?? m[3] ?? m[4] ?? "";
  return atributos;
}

/** El bloque `<nav data-…>…</nav>` de la página, sin comentarios. */
function bloque(html, marca) {
  const limpio = html.replace(/<!--[\s\S]*?-->/g, "");
  const inicio = limpio.search(new RegExp(`<nav\\b[^>]*\\b${marca}\\b`));
  assert.notEqual(inicio, -1, `no hay <nav ${marca}>`);
  return limpio.slice(inicio, limpio.indexOf("</nav>", inicio));
}

/** Los elementos `a`/`span` de esa clase en el trozo: `[{nombre, atributos, texto}]`. */
function elementosDeClase(trozo, clase) {
  const vistos = [];
  for (const m of trozo.matchAll(ETIQUETA)) {
    const atributos = atributosDe(m[2]);
    if ((atributos.class || "").split(/\s+/).includes(clase)) {
      const texto = m[3].replace(/<span class="rs-recorrido__num"[^>]*>\d+<\/span>/, "").replace(/<[^>]+>/g, "");
      vistos.push({ nombre: m[1], atributos, texto: texto.replace(/\s+/g, " ").trim() });
    }
  }
  return vistos;
}

/** Lo que incumple un enlace a la bandeja según T6a: lista vacía = correcto. */
function problemasDelEnlace(quien, e) {
  const problemas = [];
  if (!e) return [`${quien}: no está`];
  if (e.nombre !== "a" || e.atributos.href !== "bandeja.html") {
    problemas.push(`${quien}: <${e.nombre} href="${e.atributos.href}">, no <a href="bandeja.html">`);
  }
  if ("data-construccion" in e.atributos) problemas.push(`${quien}: lleva data-construccion`);
  if (/en construcción/.test(e.atributos["aria-label"] || "")) {
    problemas.push(`${quien}: aria-label «${e.atributos["aria-label"]}»`);
  }
  for (const actual of [":aria-current", "x-bind:aria-current", "aria-current"]) {
    if (actual in e.atributos) problemas.push(`${quien}: lleva ${actual}: lleva a otra página`);
  }
  return problemas;
}

/** Lo que incumplen la pestaña y los pasos 02 y 03 de la página. */
function problemasDeLaPagina(html, pagina) {
  const pestana = elementosDeClase(bloque(html, "data-barra-portal"), "rs-pestana")
    .find((e) => e.texto === "Bandeja de revisión");
  const pasos = elementosDeClase(bloque(html, "data-recorrido"), "rs-recorrido__paso");
  return [
    ...problemasDelEnlace(`${pagina} · pestaña Bandeja de revisión`, pestana),
    ...problemasDelEnlace(`${pagina} · paso 02 Revisión`, pasos.find((e) => e.texto === "Revisión")),
    ...problemasDelEnlace(`${pagina} · paso 03 Sigrid`, pasos.find((e) => e.texto === "Sigrid")),
  ];
}

// ── La fuente: enlaceSeccion ────────────────────────────────────────────────

test("f040 T6a: enlaceSeccion('bandeja') da bandeja.html desde el portal, el circuito y las páginas de entrada", () => {
  const { enlaceSeccion } = portal();

  for (const [pagina, desde] of PAGINAS_QUE_ENLAZAN_LA_BANDEJA) {
    assert.deepEqual(enlaceSeccion("bandeja", desde), { href: "bandeja.html", nuevaPestana: false }, pagina);
  }
  assert.equal(enlaceSeccion("bandeja", "bandeja.html"), null, "en bandeja.html es su sección, la actual");
});

test("f040 T6a: las demás secciones no cambian de enlace", () => {
  const { enlaceSeccion } = portal();

  assert.deepEqual(enlaceSeccion("incidencias", "portal"), { href: "#/incidencias", nuevaPestana: false });
  assert.deepEqual(enlaceSeccion("incidencias", "circuito"), { href: "./#/incidencias", nuevaPestana: false });
  assert.deepEqual(enlaceSeccion("entrada", "bandeja.html"), { href: "./#/entrada", nuevaPestana: false });
  assert.deepEqual(enlaceSeccion("partes", "portal"), { href: "partes.html", nuevaPestana: false });
  assert.equal(enlaceSeccion("partes", "circuito"), null, "partes es el circuito");
});

test("f040 T6a: la ruta #/bandeja de la maqueta sigue existiendo y la sección sigue en construcción", () => {
  const { resolverRuta, enConstruccion } = portal();

  assert.equal(resolverRuta("#/bandeja", []).seccion, "bandeja");
  assert.equal(enConstruccion("bandeja"), true, "R62: ninguna ficha de la sección está done");
});

// ── La marca: marcadaEnConstruccion ─────────────────────────────────────────

test("f040 T6a: marcadaEnConstruccion: lo que lleva a bandeja.html no se marca; lo que lleva a la maqueta, sí", () => {
  const { marcadaEnConstruccion } = portal();

  for (const [pagina, desde] of PAGINAS_QUE_ENLAZAN_LA_BANDEJA) {
    assert.equal(marcadaEnConstruccion("bandeja", desde), false, pagina);
    assert.equal(marcadaEnConstruccion("incidencias", desde), true, `${pagina}: incidencias va a la maqueta`);
    assert.equal(marcadaEnConstruccion("entrada", desde), false, `${pagina}: entrada no está en construcción`);
  }
  assert.equal(
    marcadaEnConstruccion("bandeja", "bandeja.html"), true,
    "la pestaña actual de bandeja.html, sin enlace, sigue a su sección (R2 de F-038)",
  );
  assert.equal(marcadaEnConstruccion("no-existe", "portal"), false);
  assert.equal(marcadaEnConstruccion("bandeja", "otra.html"), true, "un desde desconocido: la de la sección");
});

// ── El HTML: pestaña, pasos y tarjeta ───────────────────────────────────────

for (const [pagina] of PAGINAS_QUE_ENLAZAN_LA_BANDEJA) {
  test(`f040 T6a: en ${pagina}, la pestaña y los pasos 02 y 03 van a bandeja.html, sin marca de construcción`, () => {
    assert.deepEqual(problemasDeLaPagina(leer(pagina), pagina), []);
  });
}

test("f040 T6a: ninguna pestaña, paso ni tarjeta del front enlaza la maqueta #/bandeja", () => {
  for (const pagina of ["index.html", "partes.html", "importar.html", "oficios.html", "bandeja.html"]) {
    const html = leer(pagina).replace(/<!--[\s\S]*?-->/g, "");
    const malos = [...html.matchAll(/<a\b[^>]*\bhref="(?:\.\/)?#\/bandeja"[^>]*>/g)]
      .map((m) => m[0])
      .filter((a) => /rs-pestana|rs-recorrido__paso|rs-tarjeta/.test(a));
    assert.deepEqual(malos, [], pagina);
  }
});

test("f040 T6a: la tarjeta «Bandeja de revisión» de la portada va a bandeja.html", () => {
  const html = leer("index.html").replace(/<!--[\s\S]*?-->/g, "");
  const tarjeta = [...html.matchAll(/<a\b([^>]*)>([\s\S]*?)<\/a>/g)]
    .find((m) => /\brs-tarjeta\b/.test(m[1]) && m[2].includes('<p class="rs-tarjeta__rotulo">Bandeja de revisión</p>'));

  assert.ok(tarjeta, "no se encuentra la tarjeta de la bandeja en la portada");
  assert.equal(atributosDe(tarjeta[1]).href, "bandeja.html");
});

test("f040 T6a: control: un enlace a la maqueta, una marca o un :aria-current saltan", () => {
  const pagina = "importar.html";
  const bueno = '<a href="bandeja.html" class="rs-pestana">Bandeja de revisión</a>';
  const html = leer(pagina);
  for (const [que, malo, senal] of [
    ["a la maqueta", '<a href="./#/bandeja" class="rs-pestana">Bandeja de revisión</a>', /no <a href="bandeja.html">/],
    ["con la marca", '<a href="bandeja.html" class="rs-pestana" data-construccion>Bandeja de revisión</a>', /lleva data-construccion/],
    ["con su aria-label", '<a href="bandeja.html" class="rs-pestana" aria-label="Bandeja de revisión (en construcción)">Bandeja de revisión</a>', /aria-label/],
    ["con :aria-current", `<a href="bandeja.html" class="rs-pestana" :aria-current="seccion === 'bandeja' ? 'page' : false">Bandeja de revisión</a>`, /lleva :aria-current/],
  ]) {
    const estropeado = html.replace(/<a\b[^>]*class="rs-pestana"[^>]*>Bandeja de revisión<\/a>/, malo);
    assert.notEqual(estropeado, html, `${que}: el control no encuentra la pestaña`);
    const problemas = problemasDeLaPagina(estropeado, pagina);
    assert.ok(problemas.some((p) => senal.test(p)), `${que}: ${problemas.join(" | ")}`);
  }
  const arreglado = html.replace(/<a\b[^>]*class="rs-pestana"[^>]*>Bandeja de revisión<\/a>/, bueno);
  assert.ok(
    !problemasDeLaPagina(arreglado, pagina).some((p) => p.includes("pestaña")),
    "la pestaña buena no da problemas",
  );
});
