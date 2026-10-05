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
//   Las barras de `importar.html` y `oficios.html` entraron en los bloques 10
//   y 11 (`PAGINAS_CON_BARRA`).
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
// Bloque 10 (`tasks.md`, T29):
//
// - **R44, R70**: `Portal.enlaceSeccion(id, desde)` con `desde` = una página de
//   `Portal.PAGINAS` (`design.md` §16.8), y la barra de `importar.html`: sus
//   ocho pestañas con esos `href`, la de su sección como `<span
//   aria-current="page">`, todo en la misma pestaña.
// - **R66** en la barra de `importar.html` (`PAGINAS_CON_BARRA` crece), y la
//   review del bloque 8, **H-7**: la forma ligada (`:data-construccion`,
//   `:aria-label`, `x-bind:…`) de los atributos de R66 cuenta como problema.
// - T30: el resultado de importar con la semántica de estados de la marca
//   (ok, atención, info) y su texto.
//
// Bloque 11 (`tasks.md`, T31):
//
// - **R44, R66, R70** en la barra de `oficios.html` (`PAGINAS_CON_BARRA` y
//   `PAGINAS_REALES_CON_BARRA` crecen), con los controles de R70 también
//   sobre ella.
// - Review del bloque 10, **O10-4**: el aviso del resultado de importar no
//   lleva ninguna variante de estado en su `class` estático (la pone el
//   `:class`; con las dos, ganaría la que vaya después en la hoja).
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

/** Las páginas que llevan la barra superior común (R66): las cuatro del front. */
const PAGINAS_CON_BARRA = ["index.html", "partes.html", "importar.html", "oficios.html"];

/** Las páginas reales (`Portal.PAGINAS`) que llevan la barra (R70): las dos. */
const PAGINAS_REALES_CON_BARRA = ["importar.html", "oficios.html"];

/**
 * Las formas ligadas de los atributos de R66 (review del bloque 8, H-7): en
 * una página de Alpine pisan al arrancar lo que el lector ve.
 */
const FORMAS_LIGADAS_R66 = [":data-construccion", "x-bind:data-construccion", ":aria-label", "x-bind:aria-label"];

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
    for (const ligada of FORMAS_LIGADAS_R66) {
      if (ligada in pestana.atributos) {
        problemas.push(`«${seccion.etiqueta}» lleva ${ligada}: Alpine pisaría lo que dice el HTML (H-7)`);
      }
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

for (const [pagina, viejo, nuevo] of [
  ["index.html", '<a href="#/bandeja"', '<a href="#/bandeja" :data-construccion="false"'],
  ["index.html", '<a href="#/incidencias"', `<a href="#/incidencias" :aria-label="'Incidencias'"`],
  ["importar.html", '<a href="./#/datos"', '<a href="./#/datos" x-bind:data-construccion="false"'],
  ["importar.html", '<a href="./#/inicio"', `<a href="./#/inicio" x-bind:aria-label="'Inicio'"`],
]) {
  test(`f035 R66 (H-7): control: ${nuevo.split(" ")[2].split("=")[0]} ligado en una pestaña de ${pagina} salta`, () => {
    // Mutaciones V5 y V6 de la review del bloque 8, en todas sus formas.
    const Portal = portal();
    const html = leer(pagina);
    const estropeado = html.replace(viejo, nuevo);

    assert.notEqual(estropeado, html, `el control no encuentra ${viejo} en ${pagina}`);
    assert.ok(
      problemasR66(estropeado, Portal).some((p) => p.includes("(H-7)")),
      `${pagina}: la forma ligada de un atributo de R66 tiene que saltar`,
    );
  });
}

// ── R44 y R70 · La barra de las páginas reales (bloque 10, T29) ─────────────
//
// `enlaceSeccion(id, desde)` acepta como `desde` una página de
// `Portal.PAGINAS` (`design.md` §16.8): la sección de la página es la actual
// (`null`), `partes` lleva al circuito y las demás al portal (`./#/<id>`),
// todo en la misma pestaña (R73 ajustado).

test("f035 R44: enlaceSeccion desde una página de PAGINAS: su sección es la actual, partes.html y ./#/<id>", () => {
  const { SECCIONES, PAGINAS, enlaceSeccion } = portal();

  for (const pagina of Object.keys(PAGINAS)) {
    for (const seccion of SECCIONES) {
      const enlace = enlaceSeccion(seccion.id, pagina);
      if (seccion.id === PAGINAS[pagina]) {
        assert.equal(enlace, null, `${pagina}: «${seccion.id}» es su sección, la actual`);
      } else if (seccion.id === "partes") {
        assert.deepEqual(enlace, { href: "partes.html", nuevaPestana: false }, `${pagina}: partes`);
      } else {
        assert.deepEqual(enlace, { href: `./#/${seccion.id}`, nuevaPestana: false }, `${pagina}: ${seccion.id}`);
      }
    }
  }
});

test("f035 R44: enlaceSeccion desde importar.html y oficios.html: Entrada es la actual", () => {
  const { enlaceSeccion } = portal();

  for (const pagina of ["importar.html", "oficios.html"]) {
    assert.equal(enlaceSeccion("entrada", pagina), null, pagina);
    assert.deepEqual(enlaceSeccion("inicio", pagina), { href: "./#/inicio", nuevaPestana: false }, pagina);
    assert.deepEqual(enlaceSeccion("bandeja", pagina), { href: "./#/bandeja", nuevaPestana: false }, pagina);
    assert.deepEqual(enlaceSeccion("partes", pagina), { href: "partes.html", nuevaPestana: false }, pagina);
  }
});

test("f035 R44: enlaceSeccion con un desde desconocido devuelve null para toda sección y no lanza", () => {
  const { SECCIONES, enlaceSeccion } = portal();

  for (const raro of ["otra.html", "partes.html", "index.html", "", undefined, null, 42, "toString", "__proto__", "constructor", "IMPORTAR.HTML"]) {
    for (const seccion of SECCIONES) {
      assert.equal(enlaceSeccion(seccion.id, raro), null, `enlaceSeccion("${seccion.id}", ${JSON.stringify(raro)})`);
    }
  }
  assert.equal(enlaceSeccion("no-existe", "importar.html"), null, "un id desconocido desde una página");
});

/**
 * Lo que la barra de una página real incumple de R70 (y R44, R73): lista
 * vacía = correcto. Las ocho pestañas en su orden; cada una con el `href` de
 * `enlaceSeccion(id, pagina)`, sin `target`, `rel` ni formas ligadas; la de
 * su sección (`PAGINAS[pagina]`), un `<span aria-current="page">` sin enlace.
 */
function problemasR70(html, pagina, Portal) {
  const { SECCIONES, PAGINAS, enlaceSeccion } = Portal;
  const pestanas = pestanasDeLaBarra(html);
  const problemas = [];
  const leidas = pestanas.map((p) => p.texto).join(" | ");
  const esperadas = SECCIONES.map((s) => s.etiqueta).join(" | ");
  if (leidas !== esperadas) problemas.push(`${pagina}: pestañas «${leidas}», no «${esperadas}»`);
  for (const seccion of SECCIONES) {
    const pestana = pestanas.find((p) => p.texto === seccion.etiqueta);
    if (!pestana) continue;
    const enlace = enlaceSeccion(seccion.id, pagina);
    for (const sobra of [":href", "x-bind:href", ":target", "x-bind:target", "target", "rel"]) {
      if (sobra in pestana.atributos) problemas.push(`${pagina}: «${seccion.etiqueta}» lleva ${sobra}`);
    }
    if (enlace === null) {
      if (seccion.id !== PAGINAS[pagina]) problemas.push(`${pagina}: «${seccion.etiqueta}» sin enlace y no es su sección`);
      if (pestana.nombre !== "span" || "href" in pestana.atributos) {
        problemas.push(`${pagina}: «${seccion.etiqueta}» es la actual: <span> sin enlace`);
      }
      if (pestana.atributos["aria-current"] !== "page") problemas.push(`${pagina}: «${seccion.etiqueta}» sin aria-current`);
      continue;
    }
    if (pestana.nombre !== "a") problemas.push(`${pagina}: «${seccion.etiqueta}» no es un enlace`);
    if (pestana.atributos.href !== enlace.href) {
      problemas.push(`${pagina}: «${seccion.etiqueta}» va a «${pestana.atributos.href}», no a «${enlace.href}»`);
    }
    if (enlace.nuevaPestana !== false) problemas.push(`${pagina}: «${seccion.etiqueta}» se abriría aparte`);
    if ("aria-current" in pestana.atributos) problemas.push(`${pagina}: «${seccion.etiqueta}» no es la actual`);
  }
  return problemas;
}

for (const pagina of PAGINAS_REALES_CON_BARRA) {
  test(`f035 R70: la barra de ${pagina} tiene las ocho pestañas, en su orden, con los href de enlaceSeccion(id, "${pagina}")`, () => {
    assert.deepEqual(problemasR70(leer(pagina), pagina, portal()), []);
  });
}

for (const [que, viejo, nuevo, senal] of [
  ["un href distinto", '<a href="./#/bandeja"', '<a href="#/bandeja"', /va a «#\/bandeja»/],
  ["la pestaña actual como enlace", '<span aria-current="page" class="rs-pestana">Entrada</span>', '<a href="./#/entrada" class="rs-pestana">Entrada</a>', /es la actual/],
  ["un target en Inicio (mutación 21)", '<a href="./#/inicio"', '<a href="./#/inicio" target="_blank"', /Inicio» lleva target/],
  ["un :href ligado", '<a href="./#/datos"', `<a href="./#/datos" :href="'./#/datos'"`, /lleva :href/],
  ["el circuito por el portal", '<a href="partes.html"', '<a href="./#/partes"', /Partes firmados» va a/],
  ["una pestaña de más marcada actual", '<a href="./#/inicio" class="rs-pestana">', '<a href="./#/inicio" aria-current="page" class="rs-pestana">', /no es la actual/],
  ["una pestaña que falta", /<a href="\.\/#\/economico"[^>]*>Coste y venta<\/a>/, "", /pestañas «/],
]) {
  for (const pagina of PAGINAS_REALES_CON_BARRA) {
    test(`f035 R70: control: ${que} en la barra de ${pagina} salta`, () => {
      const html = leer(pagina);
      const estropeado = html.replace(viejo, nuevo);
      assert.notEqual(estropeado, html, `el control no encuentra ${viejo}`);

      const problemas = problemasR70(estropeado, pagina, portal());
      assert.ok(problemas.some((p) => senal.test(p)), `${que}: R70 no lo ve:\n${problemas.join("\n")}`);
    });
  }
}

// ── T30 · La semántica de estados del resultado de importar ─────────────────
//
// Mutaciones G1 y G2 del bloque 10: el remodelado pinta el resultado con los
// colores de estado de la marca (`design.md` §16.5; R57 de lo que pinta el
// portal, aquí para la página real): completa en ok, parcial en atención y un
// fichero ya importado en info, que no es un éxito de ahora. El `:class` se
// evalúa de verdad contra lo que da `Importacion.presentarImportacion`, y el
// mismo elemento lleva el texto del estado (nunca solo color).

/** El elemento del resultado: `{clase, ligada, cuerpo}` del `<div>` con `:class` sobre `resultado.`. */
function avisoDelResultado(html) {
  const m = html.match(/<div class="([^"]*)"\s+:class="([^"]*resultado\.[^"]*)">([\s\S]*?)<\/div>/);
  assert.ok(m, "importar.html: no se encuentra el aviso del resultado (<div class=… :class=…resultado.…>)");
  return { clase: m[1], ligada: m[2], cuerpo: m[3] };
}

function claseDeEstado(ligada, resultado) {
  return Function("resultado", `"use strict"; return (${ligada});`)(resultado);
}

const RESPUESTA_BASE = {
  obra: "9999",
  estado: "completa",
  ya_importado: false,
  resumen: { leidas: 3, nuevas: 3, duplicadas_en_fichero: 0, ya_en_bandeja: 0, con_error: 0 },
  filas: [],
  errores: [],
};

/** Lo que el aviso del resultado de importar.html incumple: lista vacía = correcto. */
function problemasDeEstadosDelResultado(html) {
  const Importacion = require("../js/importacion.js");
  const { clase, ligada, cuerpo } = avisoDelResultado(html);
  const problemas = [];
  if (!clase.split(/\s+/).includes("rs-aviso")) problemas.push(`el aviso del resultado no es rs-aviso: «${clase}»`);
  const fijas = clase.split(/\s+/).filter((c) => /^rs-aviso--(?:ok|atencion|error|info)$/.test(c));
  if (fijas.length) problemas.push(`el aviso del resultado lleva ${fijas.join(" ")} fijo: el estado lo pone el :class (O10-4)`);
  if (!/x-text="resultado\.estadoTexto"/.test(cuerpo)) problemas.push("el aviso del resultado no lleva el texto del estado");
  for (const [que, cambios, esperada] of [
    ["completa", {}, "rs-aviso--ok"],
    ["parcial", { estado: "parcial" }, "rs-aviso--atencion"],
    ["ya importado (completa)", { ya_importado: true }, "rs-aviso--info"],
    ["ya importado (parcial)", { ya_importado: true, estado: "parcial" }, "rs-aviso--info"],
  ]) {
    const resultado = Importacion.presentarImportacion({ ...RESPUESTA_BASE, ...cambios });
    let pintada;
    try {
      pintada = claseDeEstado(ligada, resultado);
    } catch (error) {
      problemas.push(`${que}: el :class lanza (${error.message})`);
      continue;
    }
    if (pintada !== esperada) problemas.push(`${que}: se pinta «${pintada}», no «${esperada}»`);
  }
  return problemas;
}

test("f035 T30: el resultado de importar se pinta con la semántica de estados y su texto", () => {
  assert.deepEqual(problemasDeEstadosDelResultado(leer("importar.html")), []);
});

for (const [que, viejo, nuevo] of [
  ["ya importado en ok (G1)", "resultado.yaImportado ? 'rs-aviso--info'", "resultado.yaImportado ? 'rs-aviso--ok'"],
  ["parcial y completa cruzadas (G2)", "'rs-aviso--atencion' : 'rs-aviso--ok'", "'rs-aviso--ok' : 'rs-aviso--atencion'"],
  ["sin el caso del ya importado", "resultado.yaImportado ? 'rs-aviso--info' : ", "false ? 'x' : "],
  ["sin el texto del estado", '<span x-text="resultado.estadoTexto"></span>', "<span></span>"],
  // O10-4 (S2 de la review del bloque 10): un --ok fijo junto al :class.
  ["una variante fija junto al :class (S2)", /<div class="rs-aviso"(\s+:class=)/, '<div class="rs-aviso rs-aviso--ok"$1'],
]) {
  test(`f035 T30: control: ${que} salta`, () => {
    const html = leer("importar.html");
    const estropeado = html.replace(viejo, nuevo);
    assert.notEqual(estropeado, html, `el control no encuentra ${viejo}`);

    assert.notDeepEqual(problemasDeEstadosDelResultado(estropeado), []);
  });
}

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

// ── Bloque 12 · R74: el resumen de un fichero ya importado ───────────────────
//
// Apunte (b) del humano (`design.md` §16.6): si el fichero ya se había
// importado, los recuentos son los de la importación ORIGINAL y se rotulan
// así, con su fecha en hora de Madrid; nunca como si hubieran entrado ahora.
// `importado_at_utc` lo añade al backend una ficha aparte (R76, F-053), así
// que hoy no llega: sin él, o si no es una fecha válida, el rótulo va sin
// fecha. `resumenTexto` y `textoDelEstado` no cambian (los fijan los tests de
// F-036, que no se tocan).

const RUTA_IMPORTACION = require.resolve("../js/importacion.js");
const ROTULO_AHORA = "Resumen de esta importación";
const ROTULO_SIN_FECHA = "Resumen de la importación original de este fichero";
const rotuloDel = (fecha) => `Resumen de la importación original del ${fecha}`;

/** `js/importacion.js` recién cargado (con la zona horaria del proceso que haya en ese momento). */
function importacionFresca() {
  delete require.cache[RUTA_IMPORTACION];
  return require("../js/importacion.js");
}

/** Corre `fn(Importacion)` con otra zona horaria en el proceso y el módulo cargado bajo ella. */
function conZonaDelProceso(zona, fn) {
  const previa = process.env.TZ;
  process.env.TZ = zona;
  try {
    return fn(importacionFresca());
  } finally {
    if (previa === undefined) delete process.env.TZ;
    else process.env.TZ = previa;
    delete require.cache[RUTA_IMPORTACION];
  }
}

const yaImportado = (fecha) => ({ ya_importado: true, importado_at_utc: fecha });

const CASOS_R74 = [
  // Sin ya_importado: lo que acaba de entrar.
  ["sin ya_importado", { ya_importado: false, importado_at_utc: "2026-03-10T09:15:00Z" }, ROTULO_AHORA],
  ["sin el campo ya_importado", {}, ROTULO_AHORA],
  // Con fecha válida.
  ["ya importado con fecha válida", yaImportado("2026-03-10T09:15:00Z"), rotuloDel("10/03/2026")],
  ["con +00:00 y microsegundos (isoformat de Python)", yaImportado("2026-03-10T09:15:00.123456+00:00"), rotuloDel("10/03/2026")],
  ["solo la fecha", yaImportado("2026-03-10"), rotuloDel("10/03/2026")],
  // Sin fecha (lo de hoy, hasta F-053).
  ["sin importado_at_utc", { ya_importado: true }, ROTULO_SIN_FECHA],
  ["importado_at_utc null", yaImportado(null), ROTULO_SIN_FECHA],
  ["importado_at_utc vacío", yaImportado(""), ROTULO_SIN_FECHA],
  // Fecha basura.
  ["texto que no es fecha", yaImportado("ayer por la tarde"), ROTULO_SIN_FECHA],
  ["30 de febrero", yaImportado("2026-02-30T10:00:00Z"), ROTULO_SIN_FECHA],
  ["mes 13", yaImportado("2026-13-01T10:00:00Z"), ROTULO_SIN_FECHA],
  ["hora 25", yaImportado("2026-03-10T25:00:00Z"), ROTULO_SIN_FECHA],
  ["minuto 60", yaImportado("2026-03-10T10:60:00Z"), ROTULO_SIN_FECHA],
  ["desfase imposible", yaImportado("2026-03-10T10:00:00+25:00"), ROTULO_SIN_FECHA],
  ["dd/mm/aaaa, que Date leería como mm/dd", yaImportado("10/03/2026"), ROTULO_SIN_FECHA],
  ["un número (epoch), no una fecha ISO", yaImportado(1773133200000), ROTULO_SIN_FECHA],
  ["un objeto", yaImportado({ fecha: "2026-03-10" }), ROTULO_SIN_FECHA],
  ["texto con una fecha dentro", yaImportado("importado el 2026-03-10T09:15:00Z"), ROTULO_SIN_FECHA],
  // T34, supervivientes de las mutaciones manuales (B3, C4, C6).
  ["una lista con una fecha", yaImportado(["2026-03-10T09:15:00Z"]), ROTULO_SIN_FECHA],
  ["segundo 60", yaImportado("2026-03-10T10:00:60Z"), ROTULO_SIN_FECHA],
  ["una fecha con cola", yaImportado("2026-03-10T09:15:00Z y algo más"), ROTULO_SIN_FECHA],
  // El día es el de Madrid, no el de UTC.
  ["23:30 UTC de un día de verano: el día siguiente en Madrid", yaImportado("2026-07-15T23:30:00Z"), rotuloDel("16/07/2026")],
  ["22:30 UTC de verano (UTC+2): ya es el día siguiente", yaImportado("2026-07-15T22:30:00Z"), rotuloDel("16/07/2026")],
  ["21:30 UTC de verano: aún el mismo día", yaImportado("2026-07-15T21:30:00Z"), rotuloDel("15/07/2026")],
  ["23:30 UTC de invierno (UTC+1): el día siguiente", yaImportado("2026-01-15T23:30:00Z"), rotuloDel("16/01/2026")],
  ["22:30 UTC de invierno: aún el mismo día", yaImportado("2026-01-15T22:30:00Z"), rotuloDel("15/01/2026")],
  ["la víspera del cambio de hora de marzo (aún UTC+1)", yaImportado("2026-03-28T23:30:00Z"), rotuloDel("29/03/2026")],
  ["el día del cambio de hora de marzo (ya UTC+2)", yaImportado("2026-03-29T22:30:00Z"), rotuloDel("30/03/2026")],
  ["la noche de fin de año", yaImportado("2026-12-31T23:30:00Z"), rotuloDel("01/01/2027")],
  ["sin zona: se lee en UTC, como dice el nombre del campo", yaImportado("2026-07-15T23:30:00"), rotuloDel("16/07/2026")],
  ["con el desfase de Madrid escrito", yaImportado("2026-07-16T01:30:00+02:00"), rotuloDel("16/07/2026")],
  ["con un desfase negativo", yaImportado("2026-07-15T20:30:00-03:00"), rotuloDel("16/07/2026")],
  // Los minutos del desfase cuentan: 03:44+05:45 son las 21:59 UTC, las 23:59 en Madrid.
  ["con un desfase de horas y minutos, sin dos puntos", yaImportado("2026-07-16T03:44:00+0545"), rotuloDel("15/07/2026")],
];

for (const [que, respuesta, esperado] of CASOS_R74) {
  test(`f035 R74: rotuloResumen, ${que}`, () => {
    const { rotuloResumen } = require("../js/importacion.js");

    assert.equal(rotuloResumen(respuesta), esperado);
  });
}

test("f035 R74: rotuloResumen nunca lanza: sin respuesta, el rótulo de esta importación", () => {
  const { rotuloResumen } = require("../js/importacion.js");

  for (const raro of [null, undefined, 0, "", "texto", [], true]) {
    assert.equal(rotuloResumen(raro), ROTULO_AHORA, `con ${JSON.stringify(raro)}`);
  }
});

for (const zona of ["America/New_York", "Pacific/Kiritimati", "UTC"]) {
  test(`f035 R74: el día sale en hora de Madrid aunque el proceso esté en ${zona}`, () => {
    conZonaDelProceso(zona, ({ rotuloResumen }) => {
      assert.equal(rotuloResumen(yaImportado("2026-07-15T23:30:00Z")), rotuloDel("16/07/2026"));
      assert.equal(rotuloResumen(yaImportado("2026-07-15T21:30:00Z")), rotuloDel("15/07/2026"));
      assert.equal(rotuloResumen(yaImportado("2026-07-15T23:30:00")), rotuloDel("16/07/2026"));
    });
  });
}

test("f035 R74: presentarImportacion lleva el rótulo; el estado y los recuentos, como siempre", () => {
  const Importacion = require("../js/importacion.js");
  const original = { ...RESPUESTA_BASE, ya_importado: true, importado_at_utc: "2026-07-15T23:30:00Z" };

  for (const [respuesta, rotulo] of [
    [RESPUESTA_BASE, ROTULO_AHORA],
    [{ ...RESPUESTA_BASE, ya_importado: true }, ROTULO_SIN_FECHA],
    [original, rotuloDel("16/07/2026")],
  ]) {
    const vista = Importacion.presentarImportacion(respuesta);
    assert.equal(vista.rotuloResumen, rotulo);
    // Los textos que fijan los tests de F-036, sin cambio (R43 de F-036).
    assert.equal(vista.resumenTexto, "3 filas leídas · 3 nuevas · 0 duplicadas en el fichero · 0 ya en la bandeja · 0 con error");
    assert.equal(vista.estadoTexto, Importacion.textoDelEstado(respuesta));
  }
  assert.equal(
    Importacion.textoDelEstado(original),
    "Este fichero ya se había importado: no se ha añadido nada a la bandeja.",
  );
});

// --- R75 · «Decididos como distintos» (bloque 13, T35) ------------------------------
//
// Apunte (a) del humano (`design.md` §16.6): en oficios, los pares cuya última
// decisión es «distinto», cada uno con un «Son el mismo» que manda la decisión
// «mismo» de ese par por `decidir()`, el camino de los demás botones (R88 y R89
// de F-036). `oficio.distintos` lo añade al backend una ficha aparte (R76,
// F-053), así que hoy no llega: sin él, `presentarPropuestas().distintos` es
// `[]` y la sección no se pinta. Lo que llegue mal formado se descarta sin
// romper la pantalla: un par que no se puede pintar ni decidir no se enseña.

function oficiosModulo() {
  return require("../js/oficios.js");
}

/** `GET /api/catalogos/propuestas` inventada, sin propuestas, grupos ni avisos. */
function propuestasSinDistintos() {
  return {
    obra: "9999",
    oficio: {
      oficios: [
        { codigo: "9001", nombre: "Oficio inventado A", grupo: ["9001"] },
        { codigo: "9002", nombre: "Oficio inventado B", grupo: ["9002"] },
        { codigo: "9003", nombre: "Pintura inventada", grupo: ["9003"] },
        { codigo: "9008", nombre: null, grupo: ["9008"] },
      ],
      grupos: [
        { etiqueta: "Oficio inventado A", codigos: ["9001"] },
        { etiqueta: "Oficio inventado B", codigos: ["9002"] },
        { etiqueta: "Pintura inventada", codigos: ["9003"] },
        { etiqueta: "9008", codigos: ["9008"] },
      ],
      propuestas: [],
      avisos: [],
    },
  };
}

/** La misma respuesta con `oficio.distintos` (lo que sea, también basura). */
function propuestasConDistintos(distintos) {
  const respuesta = propuestasSinDistintos();
  respuesta.oficio.distintos = distintos;
  return respuesta;
}

const A = "Oficio inventado A";
const B = "Oficio inventado B";
const P = "Pintura inventada";

/** `[codigo_a, codigo_b, nombre_a, nombre_b]` de cada par de la vista. */
const resumenDe = (distintos) => distintos.map((p) => [p.codigo_a, p.codigo_b, p.nombre_a, p.nombre_b]);

const CASOS_R75 = [
  // Lo que manda el contrato de §16.6.
  ["un par", [{ codigo_a: "9001", codigo_b: "9002" }], [["9001", "9002", A, B]]],
  [
    "varios pares, en su orden",
    [{ codigo_a: "9001", codigo_b: "9002" }, { codigo_a: "9001", codigo_b: "9003" }, { codigo_a: "9002", codigo_b: "9003" }],
    [["9001", "9002", A, B], ["9001", "9003", A, P], ["9002", "9003", B, P]],
  ],
  // Pares desordenados: cada par y la lista salen ordenados.
  ["un par al revés", [{ codigo_a: "9002", codigo_b: "9001" }], [["9001", "9002", A, B]]],
  [
    "la lista desordenada",
    [{ codigo_a: "9002", codigo_b: "9003" }, { codigo_a: "9003", codigo_b: "9001" }, { codigo_a: "9001", codigo_b: "9002" }],
    [["9001", "9002", A, B], ["9001", "9003", A, P], ["9002", "9003", B, P]],
  ],
  ["el mismo par dos veces, una al revés", [{ codigo_a: "9001", codigo_b: "9002" }, { codigo_a: "9002", codigo_b: "9001" }], [["9001", "9002", A, B]]],
  // Nombres que faltan: el marcador de siempre (R84, R87 de F-036).
  ["un oficio sin nombre en Sigrid", [{ codigo_a: "9001", codigo_b: "9008" }], [["9001", "9008", A, "(sin nombre en esta obra)"]]],
  ["un código que no es de la obra", [{ codigo_a: "9099", codigo_b: "9001" }], [["9001", "9099", A, "(sin nombre en esta obra)"]]],
  // Campo vacío.
  ["distintos vacío", [], []],
  ["distintos null", null, []],
  // Campo mal formado: no es una lista.
  ["distintos es un texto", "9001-9002", []],
  ["distintos es un objeto", { codigo_a: "9001", codigo_b: "9002" }, []],
  ["distintos es un número", 42, []],
  ["distintos es true", true, []],
  // Entradas mal formadas: se descartan y las buenas siguen.
  [
    "entradas que no son pares, junto a uno bueno",
    [null, undefined, "9001", 7, [], ["9001", "9002"], { codigo_a: "9001", codigo_b: "9002" }],
    [["9001", "9002", A, B]],
  ],
  ["un par sin codigo_b", [{ codigo_a: "9001" }], []],
  ["un par sin codigo_a", [{ codigo_b: "9002" }], []],
  ["un par con codigo_b null", [{ codigo_a: "9001", codigo_b: null }], []],
  ["un par de un código consigo mismo", [{ codigo_a: "9001", codigo_b: "9001" }], []],
  ["un código vacío", [{ codigo_a: "", codigo_b: "9002" }], []],
  ["un código en blanco", [{ codigo_a: "   ", codigo_b: "9002" }], []],
  ["códigos numéricos, no textos", [{ codigo_a: 9001, codigo_b: 9002 }], []],
  ["un código que es un objeto", [{ codigo_a: { codigo: "9001" }, codigo_b: "9002" }], []],
];

for (const [que, distintos, esperado] of CASOS_R75) {
  test(`f035 R75: presentarPropuestas().distintos, ${que}`, () => {
    const { presentarPropuestas } = oficiosModulo();

    assert.deepEqual(resumenDe(presentarPropuestas(propuestasConDistintos(distintos)).distintos), esperado);
  });
}

test("f035 R75: sin oficio.distintos (hasta F-053), distintos es [] y lo demás, como siempre", () => {
  const { presentarPropuestas } = oficiosModulo();

  const sin = presentarPropuestas(propuestasSinDistintos());
  const vacio = presentarPropuestas(propuestasConDistintos([]));

  assert.deepEqual(sin.distintos, []);
  assert.deepEqual(sin, vacio, "sin el campo, la vista es la de una lista vacía");
  assert.equal(sin.sinNada, true);
  assert.deepEqual(Object.keys(sin).sort(), ["avisos", "distintos", "grupos", "gruposVigentes", "obra", "propuestas", "sinNada"]);
});

test("f035 R75: cada par lleva su clave, sus códigos, sus nombres y motivos vacíos (el par() de siempre)", () => {
  const { presentarPropuestas } = oficiosModulo();

  const [par] = presentarPropuestas(propuestasConDistintos([{ codigo_a: "9002", codigo_b: "9001" }])).distintos;

  assert.deepEqual(par, {
    clave: "9001-9002",
    codigo_a: "9001",
    codigo_b: "9002",
    nombre_a: A,
    nombre_b: B,
    motivos: [],
  });
});

test("f035 R75: las claves de los pares son distintas entre sí (el :key del x-for)", () => {
  const { presentarPropuestas } = oficiosModulo();

  const { distintos } = presentarPropuestas(
    propuestasConDistintos([{ codigo_a: "9001", codigo_b: "9002" }, { codigo_a: "9001", codigo_b: "9003" }, { codigo_a: "9002", codigo_b: "9003" }]),
  );

  assert.equal(new Set(distintos.map((p) => p.clave)).size, 3);
});

test("f035 R75: presentarPropuestas nunca lanza por distintos, ni sin respuesta", () => {
  const { presentarPropuestas } = oficiosModulo();

  for (const raro of [null, undefined, {}, { obra: "9999" }, { obra: "9999", oficio: null }, { obra: "9999", oficio: {} }]) {
    assert.deepEqual(presentarPropuestas(raro).distintos, [], `con ${JSON.stringify(raro)}`);
  }
  for (const raro of [0, "", "x", 42, true, {}, { length: 2 }, [[]], [{}], [{ codigo_a: [] }]]) {
    assert.deepEqual(presentarPropuestas(propuestasConDistintos(raro)).distintos, [], `con distintos ${JSON.stringify(raro)}`);
  }
});

test("f035 R75: sinNada cuenta los distintos: con solo distintos hay algo que enseñar", () => {
  const { presentarPropuestas } = oficiosModulo();

  assert.equal(presentarPropuestas(propuestasConDistintos([{ codigo_a: "9001", codigo_b: "9002" }])).sinNada, false);
  assert.equal(presentarPropuestas(propuestasConDistintos([])).sinNada, true);
  assert.equal(presentarPropuestas(propuestasConDistintos([{ codigo_a: "9001" }])).sinNada, true, "un par descartado no cuenta");
  assert.equal(presentarPropuestas(propuestasConDistintos("basura")).sinNada, true);
});

test("f035 R75: los distintos no cambian propuestas, grupos ni avisos", () => {
  const { presentarPropuestas } = oficiosModulo();

  const sin = presentarPropuestas(propuestasSinDistintos());
  const con = presentarPropuestas(propuestasConDistintos([{ codigo_a: "9001", codigo_b: "9002" }]));

  for (const clave of ["obra", "propuestas", "grupos", "avisos", "gruposVigentes"]) {
    assert.deepEqual(con[clave], sin[clave], clave);
  }
});

// El botón «Son el mismo» de la sección, leído de `oficios.html` y evaluado
// con el componente de verdad (`crearAppOficios` con un `api` doble): lo que
// manda es lo que el HTML dice, no lo que el test supone.

const BOTON = /<button((?:\s+[^\s"'=<>\/]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'>]+))?)*)\s*>([^<]*)<\/button>/g;

/** `[{atributos, texto}]` de los botones de la sección `x-show="vista.distintos.length"` de `oficios.html`. */
function botonesDeDistintos() {
  const html = leer("oficios.html").replace(/<!--[\s\S]*?-->/g, "");
  const inicio = html.search(/<section\b[^>]*\bx-show="vista\.distintos\.length"/);
  assert.notEqual(inicio, -1, 'oficios.html no tiene <section x-show="vista.distintos.length">');
  const seccionHtml = html.slice(inicio, html.indexOf("</section>", inicio));
  return [...seccionHtml.matchAll(BOTON)].map((m) => ({
    atributos: atributosDe(m[1]),
    texto: m[2].replace(/\s+/g, " ").trim(),
  }));
}

/** Una expresión de Alpine evaluada como la evalúa Alpine: con el componente y el `par` del `x-for` en el ámbito. */
function evaluar(expresion, app, par) {
  return vm.runInNewContext(expresion, {
    par,
    decidir: (...args) => app.decidir(...args),
    puedeDecidir: () => app.puedeDecidir(),
  });
}

function componenteDeOficios(guion) {
  const llamadas = [];
  const respuestas = Object.assign(
    {
      identidad: { usuarioOid: "oid-inventado", correo: "" },
      propuestasCatalogos: propuestasConDistintos([{ codigo_a: "9002", codigo_b: "9001" }]),
      decidirCatalogos: { obra: "9999", pares_guardados: [] },
    },
    guion || {},
  );
  const api = {};
  for (const nombre of ["identidad", "propuestasCatalogos", "decidirCatalogos"]) {
    api[nombre] = async (...args) => {
      llamadas.push({ nombre, args });
      return respuestas[nombre];
    };
  }
  const app = oficiosModulo().crearAppOficios({ api, guardar: () => {} });
  return { app, llamadas };
}

test("f035 R75: la sección de distintos tiene un solo botón, «Son el mismo»", () => {
  const botones = botonesDeDistintos();

  assert.deepEqual(botones.map((b) => b.texto), ["Son el mismo"]);
  assert.equal(botones[0].atributos.type, "button");
});

test("f035 R75: «Son el mismo» de un par manda «mismo» con sus dos códigos y la pantalla recarga", async () => {
  const [boton] = botonesDeDistintos();
  const { app, llamadas } = componenteDeOficios();
  await app.iniciar();
  app.obra = "9999";
  await app.cargar();
  const [par] = app.vista.distintos;
  app.obra = "otra-escrita-despues";

  assert.equal(evaluar(boton.atributos[":disabled"], app, par), false, "con sesión y sin otra guardándose, se puede pulsar");
  await evaluar(boton.atributos["@click"], app, par);

  const decisiones = llamadas.filter((l) => l.nombre === "decidirCatalogos");
  assert.equal(decisiones.length, 1);
  assert.deepEqual(decisiones[0].args[0], {
    obra: "9999",
    usuario_oid: "oid-inventado",
    confirmado: true,
    decisiones: [{ catalogo: "oficio", codigos: ["9001", "9002"], decision: "mismo" }],
  });
  assert.deepEqual(
    llamadas.map((l) => l.nombre),
    ["identidad", "propuestasCatalogos", "decidirCatalogos", "propuestasCatalogos"],
    "guarda y recarga (R89 de F-036)",
  );
  assert.equal(llamadas[3].args[0], "9999", "recarga la obra de las propuestas, no la del campo");
});

test("f035 R75: sin sesión, «Son el mismo» está deshabilitado y no manda nada", async () => {
  const [boton] = botonesDeDistintos();
  const { app, llamadas } = componenteDeOficios({ identidad: { usuarioOid: "", correo: "" } });
  await app.iniciar();
  app.obra = "9999";
  await app.cargar();
  const [par] = app.vista.distintos;

  assert.equal(evaluar(boton.atributos[":disabled"], app, par), true);
  await evaluar(boton.atributos["@click"], app, par);

  assert.equal(llamadas.filter((l) => l.nombre === "decidirCatalogos").length, 0);
});

test("f035 R75: mientras se guarda otra decisión, «Son el mismo» está deshabilitado", async () => {
  const [boton] = botonesDeDistintos();
  const { app } = componenteDeOficios();
  await app.iniciar();
  app.obra = "9999";
  await app.cargar();
  const [par] = app.vista.distintos;

  app.decidiendo = true;
  assert.equal(evaluar(boton.atributos[":disabled"], app, par), true);
  app.decidiendo = false;
  assert.equal(evaluar(boton.atributos[":disabled"], app, par), false);
});
