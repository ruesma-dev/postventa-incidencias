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
// El módulo se carga DENTRO de cada test, como en `portal.test.js`: en la
// fase RED un `require` de cabecera tumbaría el fichero entero sin nombre de
// requisito.

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
