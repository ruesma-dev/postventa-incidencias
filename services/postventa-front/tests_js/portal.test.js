// services/postventa-front/tests_js/portal.test.js
// F-035 · La lógica del portal de posventa (`js/portal.js`) y su componente
// de Alpine (`js/portal_app.js`), más el cruce de los dos catálogos con el
// HTML de las dos páginas.
//
// - `js/portal.js` es **puro**: catálogos (`SECCIONES`, `PLACEHOLDERS`,
//   `ESTADOS`) y funciones sin DOM, sin Alpine y sin red (`design.md` §8.1).
// - `js/portal_app.js` es pegamento (`design.md` §8.2): aquí se **instancia**
//   con un `window` falso cuyo `fetch` y `XMLHttpRequest` fallan si se les
//   llama, y se recorren todas las secciones, todas las fichas y todo el
//   catálogo de placeholders (R16).
// - `index.html` (el portal) y `partes.html` (el circuito, mudado de
//   `index.html` en T8) se leen como texto y se cruzan con los catálogos: los
//   placeholders con su ficha (R9) y la barra superior común con
//   `Portal.SECCIONES` y `Portal.enlaceSeccion` (R31, R44).
//
// Los módulos se cargan DENTRO de cada test y no en la cabecera: en la fase
// RED no existen, y un `require` de cabecera tumbaría el fichero entero con
// un solo error sin nombre de requisito.
//
// Todos los datos de las funciones puras son INVENTADOS y evidentemente
// ficticios (R24): obras 99NN, partes RS99…, «(ejemplo)». Los catálogos de
// Sigrid, con sus códigos reales (D-10).

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const RAIZ_FRONT = path.resolve(__dirname, "..");

function portal() {
  return require("../js/portal.js");
}

function datos() {
  return require("../js/maqueta_datos.js");
}

function componente() {
  return require("../js/portal_app.js");
}

function leer(relativa) {
  return fs.readFileSync(path.join(RAIZ_FRONT, relativa), "utf8");
}

// ── Un lector de HTML mínimo ────────────────────────────────────────────────
//
// Node no trae parser de HTML y el front no tiene dependencias. Esto basta
// para lo que se mira aquí: etiquetas, atributos (entre comillas, que en
// Alpine llevan `>` y `<` dentro) y texto. Los comentarios se saltan; el
// contenido de `<script>` y `<style>` no se interpreta.

const VACIOS = new Set([
  "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
  "source", "track", "wbr",
]);
const TEXTO_CRUDO = new Set(["script", "style"]);
const ATRIBUTO = /([^\s"'=<>\/]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+)))?/g;

function atributosDe(trozo) {
  const atributos = {};
  for (const m of trozo.matchAll(ATRIBUTO)) {
    const valor = m[2] !== undefined ? m[2] : m[3] !== undefined ? m[3] : m[4];
    atributos[m[1]] = valor === undefined ? "" : valor;
  }
  return atributos;
}

/** Árbol `{nombre, atributos, hijos, padre}`; los textos son `{texto}`. */
function arbol(html) {
  const raiz = { nombre: "#documento", atributos: {}, hijos: [], padre: null };
  let actual = raiz;
  let i = 0;
  while (i < html.length) {
    if (html.startsWith("<!--", i)) {
      const fin = html.indexOf("-->", i + 4);
      i = fin === -1 ? html.length : fin + 3;
      continue;
    }
    const esEtiqueta = html[i] === "<" && /[a-zA-Z\/!]/.test(html[i + 1] || "");
    if (!esEtiqueta) {
      const siguiente = html.indexOf("<", i + 1);
      const fin = siguiente === -1 ? html.length : siguiente;
      actual.hijos.push({ texto: html.slice(i, fin), padre: actual });
      i = fin;
      continue;
    }
    // Fin de la etiqueta respetando las comillas de los atributos.
    let j = i + 1;
    let comilla = null;
    while (j < html.length) {
      const c = html[j];
      if (comilla) {
        if (c === comilla) comilla = null;
      } else if (c === '"' || c === "'") {
        comilla = c;
      } else if (c === ">") {
        break;
      }
      j += 1;
    }
    const dentro = html.slice(i + 1, j);
    i = j + 1;
    if (dentro.startsWith("!")) continue; // <!doctype>
    if (dentro.startsWith("/")) {
      const nombre = dentro.slice(1).trim().toLowerCase();
      let n = actual;
      while (n && n.nombre !== nombre) n = n.padre;
      if (n && n.padre) actual = n.padre;
      continue;
    }
    const nombre = (dentro.match(/^[^\s\/>]+/) || [""])[0].toLowerCase();
    const nodo = {
      nombre,
      atributos: atributosDe(dentro.slice(nombre.length)),
      hijos: [],
      padre: actual,
    };
    actual.hijos.push(nodo);
    if (TEXTO_CRUDO.has(nombre)) {
      const cierre = html.toLowerCase().indexOf(`</${nombre}`, i);
      const fin = cierre === -1 ? html.length : cierre;
      nodo.hijos.push({ texto: html.slice(i, fin), padre: nodo });
      i = fin;
      continue;
    }
    if (!VACIOS.has(nombre) && !dentro.trimEnd().endsWith("/")) actual = nodo;
  }
  return raiz;
}

/** Elementos descendientes, en orden de documento. */
function elementos(nodo) {
  const lista = [];
  for (const hijo of nodo.hijos || []) {
    if (hijo.nombre) {
      lista.push(hijo);
      lista.push(...elementos(hijo));
    }
  }
  return lista;
}

function texto(nodo) {
  if (nodo.texto !== undefined) return nodo.texto;
  if (TEXTO_CRUDO.has(nodo.nombre)) return "";
  return nodo.hijos.map(texto).join("");
}

function textoLimpio(nodo) {
  return texto(nodo).replace(/\s+/g, " ").trim();
}

function barraDe(relativa) {
  const doc = arbol(leer(relativa));
  const barras = elementos(doc).filter((e) => "data-barra-portal" in e.atributos);
  assert.equal(barras.length, 1, `${relativa}: tiene que haber una y solo una <nav data-barra-portal>`);
  assert.equal(barras[0].nombre, "nav", `${relativa}: la barra superior es un <nav>`);
  return { doc, barra: barras[0] };
}

/** Las pestañas de la barra: enlaces y la marca de página actual, por etiqueta. */
function pestanasDe(barra, etiquetas) {
  return elementos(barra).filter(
    (e) => (e.nombre === "a" || "aria-current" in e.atributos) && etiquetas.has(textoLimpio(e)),
  );
}

function esAncestro(posible, nodo) {
  for (let n = nodo.padre; n; n = n.padre) if (n === posible) return true;
  return false;
}

// ── Dobles de red para el componente (R16) ──────────────────────────────────

/**
 * Ejecuta `cuerpo` con un `window` falso y la red prohibida. `fetch` y
 * `XMLHttpRequest` —en `window` y como globales— fallan y dejan constancia.
 */
function conVentanaFalsa(cuerpo) {
  const llamadas = [];
  const oyentes = {};
  const fetchQueFalla = (...args) => {
    llamadas.push(`fetch(${args.map(String).join(", ")})`);
    throw new Error("R16: la maqueta ha llamado a fetch");
  };
  function XhrQueFalla() {
    llamadas.push("new XMLHttpRequest()");
    throw new Error("R16: la maqueta ha creado un XMLHttpRequest");
  }
  const ventana = {
    Portal: portal(),
    MaquetaDatos: datos(),
    location: { hash: "" },
    addEventListener(tipo, fn) {
      (oyentes[tipo] = oyentes[tipo] || []).push(fn);
    },
    removeEventListener() {},
    fetch: fetchQueFalla,
    XMLHttpRequest: XhrQueFalla,
  };
  const previos = {};
  const globales = {
    window: ventana,
    location: ventana.location,
    fetch: fetchQueFalla,
    XMLHttpRequest: XhrQueFalla,
  };
  for (const [clave, valor] of Object.entries(globales)) {
    previos[clave] = Object.getOwnPropertyDescriptor(globalThis, clave);
    Object.defineProperty(globalThis, clave, { value: valor, configurable: true, writable: true });
  }
  try {
    return cuerpo({ ventana, oyentes, llamadas });
  } finally {
    for (const [clave, descriptor] of Object.entries(previos)) {
      if (descriptor) Object.defineProperty(globalThis, clave, descriptor);
      else delete globalThis[clave];
    }
  }
}

/** `ir()` y, si el componente escucha `hashchange`, se le avisa como haría el navegador. */
function navegar(c, oyentes, seccion, incidencia) {
  c.ir(seccion, incidencia);
  for (const fn of oyentes.hashchange || []) fn({ type: "hashchange" });
}

function nuevoComponente() {
  const crear = componente();
  assert.equal(typeof crear, "function", "js/portal_app.js exporta la función portalPosventa");
  const c = crear();
  c.iniciar();
  return c;
}

// ── Catálogos esperados (design.md §4 y §6.3) ───────────────────────────────

const SECCIONES_ESPERADAS = [
  ["inicio", "Inicio", []],
  ["entrada", "Entrada", ["F-036", "F-037"]],
  ["bandeja", "Bandeja de revisión", ["F-038", "F-039", "F-040", "F-043"]],
  ["incidencias", "Incidencias", ["F-041", "F-042", "F-043", "F-047"]],
  ["impresion", "Impresión de partes", ["F-044"]],
  ["partes", "Partes firmados", ["F-045"]],
  ["economico", "Coste y venta", ["F-046", "F-047"]],
  ["datos", "Datos y datamart", ["F-048"]],
];

const SECCIONES_DEL_PORTAL = SECCIONES_ESPERADAS.map(([id]) => id).filter((id) => id !== "partes");

//: [id, ficha, etiqueta, enBloque] del catálogo inicial, con la enmienda del
//: 2026-09-25 (`bandeja.reintentarVolcado`). Se pueden añadir; no cambiar.
//: Los dos de F-036 (`entrada.elegirExcel`, `entrada.importar`) salieron en la
//: enmienda del 2026-10-05: F-036 está done y vive en `importar.html` (§16.5).
const PLACEHOLDERS_ESPERADOS = [
  ["entrada.verContratoWeb", "F-037", "Ver el contrato de entrada", false],
  ["bandeja.editar", "F-038", "Editar", false],
  ["bandeja.descartar", "F-038", "Descartar", false],
  ["bandeja.aprobar", "F-038", "Aprobar", false],
  ["bandeja.cambiarIndustrial", "F-039", "Cambiar industrial", false],
  ["bandeja.aprobarSeleccionadas", "F-043", "Aprobar las seleccionadas", true],
  ["bandeja.verVolcado", "F-040", "Ver qué se crearía en Sigrid", false],
  ["bandeja.volcar", "F-040", "Volcar a Sigrid", false],
  ["bandeja.reintentarVolcado", "F-040", "Reintentar los rechazados y no procesados", true],
  ["incidencias.cambiarEstadoBloque", "F-043", "Cambiar estado…", true],
  ["incidencias.asignarIndustrialBloque", "F-043", "Asignar industrial…", true],
  ["incidencias.imprimirBloque", "F-044", "Imprimir los partes", true],
  ["ficha.guardar", "F-041", "Guardar cambios", false],
  ["ficha.verCambioEstado", "F-041", "Ver qué cambiaría en Sigrid", false],
  ["ficha.aplicarEstado", "F-041", "Aplicar el cambio", false],
  ["ficha.cambiarIndustrial", "F-039", "Cambiar industrial", false],
  ["ficha.imprimir", "F-044", "Imprimir el parte", false],
  ["ficha.enviarNoProcede", "F-042", "Pasar a no procede y enviar el correo", false],
  ["ficha.registrarSinFirma", "F-045", "Registrar el parte sin firma", false],
  ["ficha.enlazarProforma", "F-047", "Enlazar proforma", false],
  ["impresion.generarPdf", "F-044", "Generar el PDF", true],
  ["impresion.imprimir", "F-044", "Imprimir", true],
  ["partes.registrarSinFirma", "F-045", "Registrar un parte sin firma", false],
  ["economico.actualizar", "F-046", "Actualizar desde Sigrid", false],
  ["datos.verDiccionario", "F-048", "Ver el diccionario en el datamart", false],
];

const AVISO_INCIDENCIA_INEXISTENTE = "Esa incidencia no existe en los datos de ejemplo";

// ── R2 · El catálogo de secciones ───────────────────────────────────────────

test("f035 R2: Portal.SECCIONES son las ocho, en su orden, con etiqueta y fichas", () => {
  const { SECCIONES } = portal();

  assert.ok(Object.isFrozen(SECCIONES), "el catálogo es de solo lectura");
  assert.deepEqual(
    SECCIONES.map((s) => s.id),
    SECCIONES_ESPERADAS.map(([id]) => id),
  );
  for (const [id, etiqueta, fichas] of SECCIONES_ESPERADAS) {
    const seccion = SECCIONES.find((s) => s.id === id);
    assert.equal(seccion.etiqueta, etiqueta, `${id}: etiqueta`);
    assert.deepEqual([...seccion.fichas].sort(), [...fichas].sort(), `${id}: fichas que la construyen`);
  }
});

test("f035 R2: solo `partes` vive fuera del portal (pagina: partes.html)", () => {
  const { SECCIONES } = portal();

  for (const seccion of SECCIONES) {
    const esperada = seccion.id === "partes" ? "partes.html" : null;
    assert.equal(seccion.pagina, esperada, `${seccion.id}: pagina`);
  }
});

// ── R4-R7 · Rutas por hash ──────────────────────────────────────────────────

test("f035 R4: #/<id> de una sección del portal la muestra, sin aviso", () => {
  const { resolverRuta } = portal();

  for (const id of SECCIONES_DEL_PORTAL) {
    const ruta = resolverRuta(`#/${id}`, ["EJ-0001"]);
    assert.equal(ruta.seccion, id, `#/${id}`);
    assert.equal(ruta.incidencia, null, `#/${id}: sin ficha abierta`);
    assert.ok(!ruta.aviso, `#/${id}: sin aviso`);
  }
});

test("f035 R4: la ruta tolera mayúsculas y la barra final", () => {
  const { resolverRuta } = portal();

  assert.equal(resolverRuta("#/BANDEJA", []).seccion, "bandeja");
  assert.equal(resolverRuta("#/bandeja/", []).seccion, "bandeja");
  assert.equal(resolverRuta("#/Economico", []).seccion, "economico");
});

test("f035 R5: un hash vacío o desconocido muestra inicio, sin error ni aviso", () => {
  const { resolverRuta } = portal();

  for (const hash of ["", "#", "#/", "#/no-existe"]) {
    const ruta = resolverRuta(hash, ["EJ-0001"]);
    assert.equal(ruta.seccion, "inicio", `«${hash}»`);
    assert.equal(ruta.incidencia, null, `«${hash}»`);
    assert.ok(!ruta.aviso, `«${hash}»: sin aviso`);
  }
});

test("f035 R5: #/partes muestra inicio (la pestaña partes es el circuito, no una sección del portal)", () => {
  const { resolverRuta } = portal();

  for (const hash of ["#/partes", "#/PARTES", "#/partes/"]) {
    const ruta = resolverRuta(hash, []);
    assert.equal(ruta.seccion, "inicio", hash);
    assert.ok(!ruta.aviso, `${hash}: sin aviso ni redirección`);
  }
});

test("f035 R6: #/incidencias/<id> de una incidencia de ejemplo abre su ficha", () => {
  const { resolverRuta } = portal();

  const ruta = resolverRuta("#/incidencias/EJ-0003", ["EJ-0001", "EJ-0003"]);

  assert.equal(ruta.seccion, "incidencias");
  assert.equal(ruta.incidencia, "EJ-0003");
  assert.ok(!ruta.aviso);
});

test("f035 R7: una incidencia que no existe muestra el listado con su aviso", () => {
  const { resolverRuta } = portal();

  const ruta = resolverRuta("#/incidencias/EJ-9999", ["EJ-0001", "EJ-0003"]);

  assert.equal(ruta.seccion, "incidencias");
  assert.equal(ruta.incidencia, null);
  assert.equal(ruta.aviso, AVISO_INCIDENCIA_INEXISTENTE);
});

test("f035 R4-R6: hashDe es la inversa de resolverRuta", () => {
  const { hashDe, resolverRuta } = portal();

  assert.equal(hashDe("bandeja"), "#/bandeja");
  assert.equal(hashDe("incidencias", "EJ-0003"), "#/incidencias/EJ-0003");
  for (const id of SECCIONES_DEL_PORTAL) {
    assert.equal(resolverRuta(hashDe(id), []).seccion, id, id);
  }
  const ficha = resolverRuta(hashDe("incidencias", "EJ-0003"), ["EJ-0003"]);
  assert.equal(ficha.incidencia, "EJ-0003");
});

test("f035 R4-R7: las incidencias de los datos de ejemplo se abren por su ruta", () => {
  const { resolverRuta, hashDe } = portal();
  const ids = datos().incidencias.filas.map((fila) => fila.id);

  for (const id of ids) {
    assert.equal(resolverRuta(hashDe("incidencias", id), ids).incidencia, id, id);
  }
});

// ── enlaceSeccion · la única fuente de los href de las dos barras ───────────

test("f035 R44: enlaceSeccion desde el portal: #/<id>, y partes.html en la misma pestaña", () => {
  const { enlaceSeccion } = portal();

  for (const id of SECCIONES_DEL_PORTAL) {
    assert.deepEqual(enlaceSeccion(id, "portal"), { href: `#/${id}`, nuevaPestana: false }, id);
  }
  assert.deepEqual(enlaceSeccion("partes", "portal"), { href: "partes.html", nuevaPestana: false });
});

test("f035 R31: enlaceSeccion desde el circuito: ./#/<id> en pestaña nueva, y partes es la página actual", () => {
  const { enlaceSeccion } = portal();

  for (const id of SECCIONES_DEL_PORTAL) {
    assert.deepEqual(enlaceSeccion(id, "circuito"), { href: `./#/${id}`, nuevaPestana: true }, id);
  }
  assert.equal(enlaceSeccion("partes", "circuito"), null);
});

test("f035 R44: enlaceSeccion con un id desconocido devuelve null y no lanza", () => {
  const { enlaceSeccion } = portal();

  assert.equal(enlaceSeccion("no-existe", "portal"), null);
  assert.equal(enlaceSeccion("no-existe", "circuito"), null);
  assert.equal(enlaceSeccion(undefined, "portal"), null);
});

// ── R8 · El catálogo de placeholders ────────────────────────────────────────

test("f035 R8: cada placeholder tiene id único, ficha F-0NN, etiqueta, explicación y enBloque", () => {
  const { PLACEHOLDERS } = portal();

  assert.ok(Object.isFrozen(PLACEHOLDERS), "el catálogo es de solo lectura");
  const ids = PLACEHOLDERS.map((p) => p.id);
  assert.equal(new Set(ids).size, ids.length, "hay ids de placeholder repetidos");
  for (const p of PLACEHOLDERS) {
    assert.ok(p.id, "un placeholder sin id");
    assert.match(p.ficha, /^F-0\d\d$/, `${p.id}: ficha`);
    assert.notEqual(p.ficha, "F-035", `${p.id}: F-035 no puede tener placeholders (R28 la dejaría viva)`);
    assert.ok(p.etiqueta, `${p.id}: etiqueta`);
    assert.ok(p.explicacion, `${p.id}: explicación`);
    assert.equal(typeof p.enBloque, "boolean", `${p.id}: enBloque`);
  }
});

test("f035 R8: están los placeholders del inventario, con su ficha, etiqueta y enBloque", () => {
  const { PLACEHOLDERS } = portal();

  for (const [id, ficha, etiqueta, enBloque] of PLACEHOLDERS_ESPERADOS) {
    const p = PLACEHOLDERS.find((x) => x.id === id);
    assert.ok(p, `falta el placeholder ${id}`);
    assert.equal(p.ficha, ficha, `${id}: ficha`);
    assert.equal(p.etiqueta, etiqueta, `${id}: etiqueta`);
    assert.equal(p.enBloque, enBloque, `${id}: enBloque`);
  }
});

test("f035 R8: el volcado explica que va por obra y que reintentar no duplica", () => {
  const { placeholderPorId } = portal();

  for (const id of ["bandeja.verVolcado", "bandeja.volcar"]) {
    const { explicacion } = placeholderPorId(id);
    assert.match(explicacion, /obra/i, `${id}: el volcado va por obra`);
    assert.match(explicacion, /PVI-/, `${id}: la referencia PVI- evita duplicar`);
  }
});

test("f035 R8: placeholderPorId encuentra cada entrada y devuelve null si no existe", () => {
  const { PLACEHOLDERS, placeholderPorId } = portal();

  for (const p of PLACEHOLDERS) assert.equal(placeholderPorId(p.id), p, p.id);
  assert.equal(placeholderPorId("no.existe"), null);
});

// ── R11 y R12 · El aviso de un placeholder ──────────────────────────────────

test("f035 R11: el aviso dice qué ficha lo construye y qué hará", () => {
  const { PLACEHOLDERS, textoPlaceholder } = portal();

  for (const p of PLACEHOLDERS) {
    const aviso = textoPlaceholder(p.id);
    assert.match(
      aviso,
      new RegExp(`^Todavía no hace nada: lo construye ${p.ficha} · \\S`),
      `${p.id}: «${aviso}»`,
    );
    assert.ok(aviso.includes(p.explicacion), `${p.id}: el aviso lleva la frase del catálogo`);
  }
});

test("f035 R11: un id desconocido da un texto genérico y no lanza", () => {
  const { textoPlaceholder } = portal();

  const aviso = textoPlaceholder("no.existe");

  assert.equal(typeof aviso, "string");
  assert.ok(aviso.length > 0);
});

test("f035 R12: una operación en bloque dice a cuántas incidencias afectaría", () => {
  const { textoPlaceholder } = portal();

  const aviso = textoPlaceholder("incidencias.cambiarEstadoBloque", { seleccionadas: 3 });

  assert.match(aviso, /^Todavía no hace nada: lo construye F-043 · /);
  assert.match(aviso, /\b3 incidencias\b/);
});

test("f035 R12: un placeholder que no es en bloque no habla de la selección", () => {
  const { textoPlaceholder } = portal();

  const aviso = textoPlaceholder("ficha.guardar", { seleccionadas: 3 });

  assert.doesNotMatch(aviso, /\b3 incidencias\b/);
});

test("f035 R12: con una sola seleccionada, el aviso va en singular", () => {
  const { textoPlaceholder } = portal();

  const aviso = textoPlaceholder("incidencias.cambiarEstadoBloque", { seleccionadas: 1 });

  assert.match(aviso, / 1 incidencia\.$/);
});

// ── R19 y R20 · Filtros y selección, solo en pantalla ───────────────────────

const INCIDENCIAS_INVENTADAS = Object.freeze([
  Object.freeze({
    id: "EJ-0001",
    cod: "RS99.01/0001",
    obra: "9901",
    estado: "PTE",
    descripcionCorta: "Humedad en el techo del baño (ejemplo)",
    descripcionLarga: "Mancha de humedad junto al extractor (ejemplo)",
  }),
  Object.freeze({
    id: "EJ-0002",
    cod: "RS99.01/0002",
    obra: "9902",
    estado: "SAT",
    descripcionCorta: "Puerta de armario descuadrada (ejemplo)",
    descripcionLarga: "Carpintería de madera: la hoja roza el marco (ejemplo)",
  }),
  Object.freeze({
    id: "EJ-0003",
    cod: "RS99.02/0003",
    obra: "9901",
    estado: "SAT",
    descripcionCorta: "Grifo del lavabo gotea (ejemplo)",
    descripcionLarga: "Goteo continuo en el lavabo (ejemplo)",
  }),
]);

const ids = (filas) => filas.map((f) => f.id);

test("f035 R19: con los filtros vacíos se ven todas las incidencias", () => {
  const { filtrarIncidencias } = portal();

  assert.deepEqual(ids(filtrarIncidencias(INCIDENCIAS_INVENTADAS, {})), ["EJ-0001", "EJ-0002", "EJ-0003"]);
  assert.deepEqual(
    ids(filtrarIncidencias(INCIDENCIAS_INVENTADAS, { estado: "", obra: "", texto: "" })),
    ["EJ-0001", "EJ-0002", "EJ-0003"],
  );
});

test("f035 R19: se filtra por estado, por obra y por texto, cada uno por su lado", () => {
  const { filtrarIncidencias } = portal();

  assert.deepEqual(ids(filtrarIncidencias(INCIDENCIAS_INVENTADAS, { estado: "SAT" })), ["EJ-0002", "EJ-0003"]);
  assert.deepEqual(ids(filtrarIncidencias(INCIDENCIAS_INVENTADAS, { obra: "9901" })), ["EJ-0001", "EJ-0003"]);
  assert.deepEqual(ids(filtrarIncidencias(INCIDENCIAS_INVENTADAS, { texto: "grifo" })), ["EJ-0003"]);
});

test("f035 R19: el texto busca en código, descripción corta y larga, sin mayúsculas ni tildes", () => {
  const { filtrarIncidencias } = portal();

  assert.deepEqual(ids(filtrarIncidencias(INCIDENCIAS_INVENTADAS, { texto: "HUMEDAD" })), ["EJ-0001"]);
  assert.deepEqual(ids(filtrarIncidencias(INCIDENCIAS_INVENTADAS, { texto: "bano" })), ["EJ-0001"]);
  assert.deepEqual(ids(filtrarIncidencias(INCIDENCIAS_INVENTADAS, { texto: "carpinteria" })), ["EJ-0002"]);
  assert.deepEqual(ids(filtrarIncidencias(INCIDENCIAS_INVENTADAS, { texto: "RS99.02/0003" })), ["EJ-0003"]);
});

test("f035 R19: los filtros se cumplen todos a la vez", () => {
  const { filtrarIncidencias } = portal();

  assert.deepEqual(
    ids(filtrarIncidencias(INCIDENCIAS_INVENTADAS, { estado: "SAT", obra: "9901" })),
    ["EJ-0003"],
  );
  assert.deepEqual(
    ids(filtrarIncidencias(INCIDENCIAS_INVENTADAS, { estado: "SAT", obra: "9901", texto: "armario" })),
    [],
  );
});

test("f035 R19: la bandeja se filtra por origen, estado de revisión y obra, todos a la vez", () => {
  const { filtrarBandeja } = portal();
  const bandeja = [
    { id: "B1", origen: "Excel", estado: "nueva", obra: "9901" },
    { id: "B2", origen: "Web", estado: "nueva", obra: "9901" },
    { id: "B3", origen: "Excel", estado: "aprobada", obra: "9902" },
    { id: "B4", origen: "Excel", estado: "nueva", obra: "9902" },
  ];

  assert.deepEqual(ids(filtrarBandeja(bandeja, {})), ["B1", "B2", "B3", "B4"]);
  assert.deepEqual(ids(filtrarBandeja(bandeja, { origen: "Excel" })), ["B1", "B3", "B4"]);
  assert.deepEqual(ids(filtrarBandeja(bandeja, { estado: "nueva", obra: "9902" })), ["B4"]);
  assert.deepEqual(ids(filtrarBandeja(bandeja, { origen: "Web", estado: "aprobada" })), []);
});

test("f035 R20: alternarSeleccion marca y desmarca sin mutar la lista", () => {
  const { alternarSeleccion } = portal();
  const inicial = Object.freeze(["EJ-0001"]);

  const conDos = alternarSeleccion(inicial, "EJ-0002");
  const sinLaPrimera = alternarSeleccion(conDos, "EJ-0001");

  assert.deepEqual(conDos, ["EJ-0001", "EJ-0002"]);
  assert.deepEqual(sinLaPrimera, ["EJ-0002"]);
  assert.deepEqual(inicial, ["EJ-0001"], "la lista de partida no cambia");
  assert.notEqual(conDos, inicial, "devuelve una lista nueva");
});

// ── R21 y R22 · Estados y dinero ────────────────────────────────────────────

test("f035 R21: Portal.ESTADOS son los cinco de conest, por código y resumen, sin número", () => {
  const { ESTADOS } = portal();

  assert.deepEqual(
    ESTADOS.map((e) => ({ ...e })),
    [
      { cod: "SAT", res: "SIN ATENDER" },
      { cod: "PTE", res: "PENDIENTE" },
      { cod: "TER", res: "TERMINADA" },
      { cod: "NPR", res: "NO PROCEDE" },
      { cod: "CER", res: "CERRADA" },
    ],
  );
});

test("f035 R21: el estado se enseña como «código · resumen»; uno desconocido, tal cual", () => {
  const { etiquetaEstado } = portal();

  assert.equal(etiquetaEstado("PTE"), "PTE · PENDIENTE");
  assert.equal(etiquetaEstado("NPR"), "NPR · NO PROCEDE");
  assert.equal(etiquetaEstado("XYZ"), "XYZ");
});

test("f035 R22: lo no enlazado se ve «sin enlazar», nunca 0,00 €", () => {
  const { formatoImporte } = portal();

  assert.equal(formatoImporte(null), "sin enlazar");
  assert.equal(formatoImporte(undefined), "sin enlazar");
});

test("f035 R22: un cero de verdad es 0,00 €, y los importes van en formato es-ES", () => {
  const { formatoImporte } = portal();

  assert.match(formatoImporte(0), /^0,00\s€$/);
  assert.match(formatoImporte(12345.5), /^12\.345,50\s€$/);
});

test("f035 R22: un importe negativo conserva su signo", () => {
  const { formatoImporte } = portal();

  assert.match(formatoImporte(-250), /^-250,00\s€$/);
});

test("f035 R22: un valor no numérico se ve «sin enlazar», nunca NaN", () => {
  const { formatoImporte } = portal();

  assert.equal(formatoImporte("abc"), "sin enlazar");
});

// ── R39 · Catálogos por código y resumen ────────────────────────────────────

test("f035 R39: etiquetaCatalogo enseña código · resumen, el 0003 como pendiente y el vacío como sin completar", () => {
  const { etiquetaCatalogo } = portal();
  const tipos = [
    { cod: "0002", res: "PRIMER LISTADO POSTVENTA" },
    { cod: "0003", res: null },
  ];
  const oficios = [{ cod: "0143", res: "Carpintería de madera" }];

  assert.equal(etiquetaCatalogo("0002", tipos), "0002 · PRIMER LISTADO POSTVENTA");
  assert.equal(etiquetaCatalogo("0003", tipos), "0003 · Pendiente: qué es y cuándo se usa");
  assert.equal(etiquetaCatalogo("0143", oficios), "0143 · Carpintería de madera");
  assert.equal(etiquetaCatalogo(null, oficios), "sin completar");
  assert.equal(etiquetaCatalogo("9999", oficios), "9999");
});

// ── R40 · El resumen del volcado ────────────────────────────────────────────

test("f035 R40: resumenVolcado cuenta por estado con los nombres del contrato", () => {
  const { resumenVolcado } = portal();

  const resumen = resumenVolcado([
    { estado: "previsto" },
    { estado: "previsto" },
    { estado: "creado" },
    { estado: "idempotente" },
    { estado: "rechazado" },
    { estado: "no_procesado" },
    { estado: "desconocido" },
  ]);

  assert.deepEqual(resumen, {
    previstos: 2,
    creados: 1,
    idempotentes: 1,
    rechazados: 1,
    no_procesados: 1,
  });
});

test("f035 R40: resumenVolcado de una lista vacía es todo cero", () => {
  const { resumenVolcado } = portal();

  assert.deepEqual(resumenVolcado([]), {
    previstos: 0,
    creados: 0,
    idempotentes: 0,
    rechazados: 0,
    no_procesados: 0,
  });
});

test("f035 R40: etiquetaEstadoVolcado da la etiqueta legible; un estado desconocido, tal cual", () => {
  const { etiquetaEstadoVolcado } = portal();
  const estados = [
    { cod: "previsto", etiqueta: "Se crearía" },
    { cod: "no_procesado", etiqueta: "No se llegó a intentar: se puede reenviar" },
  ];

  assert.equal(etiquetaEstadoVolcado("previsto", estados), "Se crearía");
  assert.equal(etiquetaEstadoVolcado("no_procesado", estados), "No se llegó a intentar: se puede reenviar");
  assert.equal(etiquetaEstadoVolcado("raro", estados), "raro");
  assert.equal(etiquetaEstadoVolcado("previsto", []), "previsto");
});

test("f035 R40: el resumen de los dos resultados de ejemplo sale de sus filas", () => {
  const { resumenVolcado } = portal();
  const { dryRun, hecho } = datos().volcado;

  assert.equal(resumenVolcado(dryRun.partes).creados, 0, "un dry-run no crea nada");
  assert.ok(resumenVolcado(dryRun.partes).previstos > 0);
  assert.equal(resumenVolcado(hecho.partes).previstos, 0, "un volcado hecho no deja previstos");
  assert.ok(resumenVolcado(hecho.partes).creados > 0);
});

// ── R16 · El componente no llama a nada ─────────────────────────────────────

test("f035 R16: navegar por todas las secciones, fichas y rutas no llama ni a fetch ni a XMLHttpRequest", () => {
  conVentanaFalsa(({ oyentes, llamadas }) => {
    const c = nuevoComponente();
    const idsIncidencia = datos().incidencias.filas.map((fila) => fila.id);

    for (const [id] of SECCIONES_ESPERADAS) navegar(c, oyentes, id);
    for (const id of idsIncidencia) navegar(c, oyentes, "incidencias", id);
    navegar(c, oyentes, "incidencias", "EJ-9999");
    navegar(c, oyentes, "no-existe");

    assert.deepEqual(llamadas, [], "la maqueta ha intentado salir de la pantalla");
  });
});

test("f035 R16: pulsar todos los placeholders del catálogo no llama a nada y deja su aviso (R11)", () => {
  conVentanaFalsa(({ oyentes, llamadas }) => {
    const c = nuevoComponente();

    for (const p of portal().PLACEHOLDERS) {
      c.placeholder(p.id);
      assert.match(String(c.aviso), new RegExp(`lo construye ${p.ficha}`), `${p.id}: aviso`);
      assert.ok(String(c.aviso).includes(p.explicacion), `${p.id}: el aviso lleva la frase del catálogo`);
    }

    assert.deepEqual(llamadas, [], "un placeholder ha intentado salir de la pantalla");
  });
});

test("f035 R12: en el componente, el aviso en bloque cuenta la selección de incidencias", () => {
  conVentanaFalsa(({ oyentes }) => {
    const c = nuevoComponente();
    const [primera, segunda] = datos().incidencias.filas.map((fila) => fila.id);

    c.seleccionIncidencias = [primera, segunda];
    c.placeholder("incidencias.cambiarEstadoBloque");

    assert.match(String(c.aviso), /\b2 incidencias\b/);
  });
});

test("f035 R20: la selección se conserva al cambiar de sección", () => {
  conVentanaFalsa(({ oyentes }) => {
    const c = nuevoComponente();
    const [primera] = datos().incidencias.filas.map((fila) => fila.id);

    c.seleccionIncidencias = [primera];
    navegar(c, oyentes, "bandeja");
    navegar(c, oyentes, "incidencias");

    assert.deepEqual([...c.seleccionIncidencias], [primera]);
  });
});

// ── R4-R7 · El cableado de rutas del componente (review 1, H-R1) ────────────
//
// `resolverRuta` está probada arriba como función pura; aquí se prueba que el
// componente la ESCUCHA y copia su resultado a lo que ve la pantalla
// (`seccion`, `incidenciaAbierta`, `avisoRuta`). Sin estos tests, un portal
// que nunca sale de inicio pasaba toda la suite.

test("f035 R4: en el componente, navegar a #/bandeja muestra la bandeja", () => {
  conVentanaFalsa(({ oyentes }) => {
    const c = nuevoComponente();

    navegar(c, oyentes, "bandeja");

    assert.equal(c.seccion, "bandeja");
  });
});

test("f035 R6: en el componente, #/incidencias/<id> de ejemplo abre su ficha", () => {
  conVentanaFalsa(({ oyentes }) => {
    const c = nuevoComponente();
    const [, segunda] = datos().incidencias.filas.map((fila) => fila.id);

    navegar(c, oyentes, "incidencias", segunda);

    assert.equal(c.seccion, "incidencias");
    assert.equal(c.incidenciaAbierta, segunda);
  });
});

test("f035 R7: en el componente, una incidencia que no existe da el aviso y no abre ficha", () => {
  conVentanaFalsa(({ oyentes }) => {
    const c = nuevoComponente();
    const [primera] = datos().incidencias.filas.map((fila) => fila.id);

    navegar(c, oyentes, "incidencias", primera);
    navegar(c, oyentes, "incidencias", "EJ-9999");

    assert.equal(c.seccion, "incidencias");
    assert.equal(c.avisoRuta, AVISO_INCIDENCIA_INEXISTENTE);
    assert.equal(c.incidenciaAbierta, null);
  });
});

test("f035 R5: en el componente, #/partes muestra inicio", () => {
  conVentanaFalsa(({ oyentes }) => {
    const c = nuevoComponente();

    navegar(c, oyentes, "bandeja");
    navegar(c, oyentes, "partes");

    assert.equal(c.seccion, "inicio");
  });
});

test("f035 R4: iniciar() se suscribe a hashchange y respeta el enlace profundo", () => {
  conVentanaFalsa(({ ventana, oyentes }) => {
    const c = componente()();
    ventana.location.hash = "#/bandeja";

    c.iniciar();

    assert.ok((oyentes.hashchange || []).length >= 1, "iniciar() no escucha hashchange");
    assert.equal(c.seccion, "bandeja", "un enlace profundo a #/bandeja no arranca en la bandeja");
  });
});

// ── R9 · Cada placeholder del portal, con la ficha de su entrada ────────────

test("f035 R9: cada data-placeholder de index.html lleva la ficha de su entrada en Portal.PLACEHOLDERS", () => {
  const { placeholderPorId } = portal();
  const botones = elementos(arbol(leer("index.html"))).filter((e) => "data-placeholder" in e.atributos);

  assert.ok(botones.length > 0, "index.html no tiene ni un placeholder");
  for (const boton of botones) {
    const clic = boton.atributos["@click"] || boton.atributos["x-on:click"] || "";
    const m = clic.match(/^\s*placeholder\('([^']+)'\)\s*$/);
    assert.ok(m, `un placeholder con @click «${clic}»: tiene que ser placeholder('<id>') y nada más`);
    const entrada = placeholderPorId(m[1]);
    assert.ok(entrada, `index.html pinta ${m[1]}, que no está en Portal.PLACEHOLDERS`);
    assert.equal(
      boton.atributos["data-placeholder"],
      entrada.ficha,
      `${m[1]}: data-placeholder no es la ficha de su entrada`,
    );
  }
});

test("f035 R9: todo el catálogo de placeholders está pintado en index.html", () => {
  const { PLACEHOLDERS } = portal();
  const pintados = new Set(
    elementos(arbol(leer("index.html")))
      .filter((e) => "data-placeholder" in e.atributos)
      .map((e) => ((e.atributos["@click"] || "").match(/placeholder\('([^']+)'\)/) || [])[1]),
  );

  for (const p of PLACEHOLDERS) {
    assert.ok(pintados.has(p.id), `${p.id} está en el catálogo y no se pinta en ninguna parte`);
  }
});

// ── R31 y R44 · La barra superior común ─────────────────────────────────────

for (const [pagina, modo] of [
  ["index.html", "portal"],
  ["partes.html", "circuito"],
]) {
  test(`f035 R44: la barra de ${pagina} tiene las ocho secciones de Portal.SECCIONES, en su orden`, () => {
    const { SECCIONES } = portal();
    const { barra } = barraDe(pagina);
    const etiquetas = new Set(SECCIONES.map((s) => s.etiqueta));

    assert.deepEqual(
      pestanasDe(barra, etiquetas).map(textoLimpio),
      SECCIONES.map((s) => s.etiqueta),
    );
  });

  test(`f035 R44: cada pestaña de ${pagina} enlaza a lo que da enlaceSeccion(id, "${modo}")`, () => {
    const { SECCIONES, enlaceSeccion } = portal();
    const { barra } = barraDe(pagina);
    const etiquetas = new Set(SECCIONES.map((s) => s.etiqueta));
    const pestanas = pestanasDe(barra, etiquetas);

    for (const seccion of SECCIONES) {
      const pestana = pestanas.find((p) => textoLimpio(p) === seccion.etiqueta);
      assert.ok(pestana, `${pagina}: falta la pestaña ${seccion.etiqueta}`);
      const enlace = enlaceSeccion(seccion.id, modo);
      if (enlace === null) {
        assert.ok(!("href" in pestana.atributos), `${pagina}: ${seccion.id} es la página actual, sin enlace`);
        assert.equal(pestana.atributos["aria-current"], "page", `${pagina}: ${seccion.id} lleva aria-current`);
        continue;
      }
      assert.equal(pestana.nombre, "a", `${pagina}: ${seccion.id} es un enlace`);
      assert.equal(pestana.atributos.href, enlace.href, `${pagina}: href de ${seccion.id}`);
      if (enlace.nuevaPestana) {
        assert.equal(pestana.atributos.target, "_blank", `${pagina}: ${seccion.id} se abre aparte`);
        assert.match(pestana.atributos.rel || "", /\bnoopener\b/, `${pagina}: ${seccion.id} lleva rel noopener`);
      } else {
        assert.ok(!("target" in pestana.atributos), `${pagina}: ${seccion.id} se abre en la misma pestaña`);
      }
    }
  });

  test(`f035 R44: la barra es el primer elemento de ${pagina}`, () => {
    const { doc, barra } = barraDe(pagina);
    const cuerpo = elementos(doc).find((e) => e.nombre === "body");
    assert.ok(cuerpo, `${pagina} no tiene <body>`);
    const orden = elementos(cuerpo);

    const antes = orden.slice(0, orden.indexOf(barra));
    const intrusos = antes.filter((e) => !esAncestro(e, barra));
    assert.deepEqual(
      intrusos.map((e) => `<${e.nombre}>`),
      [],
      `${pagina}: hay elementos antes de la barra superior`,
    );
  });
}

// ── Bloque 3 (T6) · Funciones puras que usa el componente ──────────────────
//
// Añadidos en T6, con su fase RED: `contadoresInicio` es de `design.md` §8.1
// y no tenía test (informe del bloque 2, §2.15); `seleccionadasPara` y
// `buscarPorId` sacan del pegamento (`portal_app.js`) las dos únicas
// decisiones que tomaría: qué selección cuenta un placeholder en bloque (R12)
// y qué fila se abre. Regla de oro de §8.2: si algo merece un test, no vive
// en el componente.

test("f035 §5.1: contadoresInicio cuenta cada fase del ciclo desde los datos", () => {
  const { contadoresInicio } = portal();
  const datosInventados = {
    bandeja: {
      filas: [
        { id: "B1", estado: "nueva" },
        { id: "B2", estado: "nueva" },
        { id: "B3", estado: "editada" },
        { id: "B4", estado: "aprobada" },
        { id: "B5", estado: "volcada" },
      ],
    },
    incidencias: {
      filas: [
        { id: "EJ-0001", estado: "SAT" },
        { id: "EJ-0002", estado: "PTE" },
        { id: "EJ-0003", estado: "PTE" },
        { id: "EJ-0004", estado: "TER" },
        { id: "EJ-0005", estado: "NPR" },
        { id: "EJ-0006", estado: "CER" },
      ],
    },
    capitulos: { filas: [{ coste: 100 }, { coste: 25.5 }, { coste: 0 }] },
  };

  assert.deepEqual(contadoresInicio(datosInventados), {
    entradasPorRevisar: 2,
    aprobadasSinVolcar: 1,
    incidenciasAbiertas: 3,
    terminadasSinCerrar: 1,
    costeDelAno: 125.5,
  });
});

test("f035 §5.1: contadoresInicio sobre los datos de ejemplo no se escribe a mano", () => {
  const { contadoresInicio } = portal();
  const d = datos();

  const c = contadoresInicio(d);

  assert.equal(c.entradasPorRevisar, d.bandeja.filas.filter((f) => f.estado === "nueva").length);
  assert.equal(c.incidenciasAbiertas, d.incidencias.filas.filter((f) => ["SAT", "PTE"].includes(f.estado)).length);
  assert.ok(c.incidenciasAbiertas > 0 && c.terminadasSinCerrar > 0, "los datos de ejemplo enseñan las dos fases");
});

test("f035 R12: seleccionadasPara cuenta la selección de la sección del placeholder", () => {
  const { seleccionadasPara } = portal();
  const selecciones = { incidencias: ["EJ-0001", "EJ-0002"], bandeja: ["BJ-0004"], impresion: [] };

  assert.equal(seleccionadasPara("incidencias.cambiarEstadoBloque", selecciones), 2);
  assert.equal(seleccionadasPara("bandeja.aprobarSeleccionadas", selecciones), 1);
  assert.equal(seleccionadasPara("impresion.generarPdf", selecciones), 0);
  assert.equal(seleccionadasPara("ficha.guardar", selecciones), 0, "la ficha no tiene selección");
  assert.equal(seleccionadasPara("no.existe", selecciones), 0);
  assert.equal(seleccionadasPara("incidencias.imprimirBloque", {}), 0, "sin lista, cero; no lanza");
});

test("f035 R6: buscarPorId devuelve la fila o null, sin lanzar", () => {
  const { buscarPorId } = portal();

  assert.equal(buscarPorId(INCIDENCIAS_INVENTADAS, "EJ-0002"), INCIDENCIAS_INVENTADAS[1]);
  assert.equal(buscarPorId(INCIDENCIAS_INVENTADAS, "EJ-9999"), null);
  assert.equal(buscarPorId(INCIDENCIAS_INVENTADAS, null), null);
  assert.equal(buscarPorId(undefined, "EJ-0001"), null);
});

// ── R57 · Los estados, en chip y con su texto (segunda ronda, T15) ──────────
//
// Con el estilo Ruesma, cada estado se pinta con su color por
// `[data-estado="<código>"]` en `css/portal.css`, pero el color nunca es la
// única pista: el chip lleva siempre su texto (código y resumen, o la
// etiqueta legible del volcado).

/** Los códigos de los tres catálogos de estado que pinta el portal. */
function codigosDeEstado() {
  const { ESTADOS } = portal();
  const d = datos();
  return [
    ...ESTADOS.map((e) => e.cod),
    ...d.bandeja.estadosRevision,
    ...d.volcado.catalogos.estados.map((e) => e.cod),
  ];
}

test("f035 R57: cada código de estado (conest, revisión y volcado) tiene su regla [data-estado] en css/portal.css", () => {
  const css = leer("css/portal.css").replace(/\/\*[\s\S]*?\*\//g, " ");
  const codigos = codigosDeEstado();

  assert.equal(codigos.length, 15, "cinco de conest, cinco de revisión y cinco de volcado");
  const faltan = codigos.filter((cod) => !css.includes(`[data-estado="${cod}"]`));
  assert.deepEqual(faltan, [], `css/portal.css no pinta estos estados: ${faltan.join(", ")}`);
});

test("f035 R57: todo elemento de index.html con data-estado es un rs-chip con su texto", () => {
  const todos = elementos(arbol(leer("index.html")));
  const conEstado = todos.filter(
    (e) => "data-estado" in e.atributos || ":data-estado" in e.atributos || "x-bind:data-estado" in e.atributos,
  );

  assert.ok(conEstado.length >= 3, "el portal pinta sus estados con data-estado");
  for (const e of conEstado) {
    const donde = `<${e.nombre} ${e.atributos[":data-estado"] || e.atributos["data-estado"] || ""}>`;
    assert.ok((e.atributos.class || "").split(/\s+/).includes("rs-chip"), `${donde}: va en un rs-chip`);
    assert.ok((e.atributos["x-text"] || "").trim(), `${donde}: el chip lleva su texto (x-text), no solo color`);
  }
  const expresiones = conEstado.map((e) => e.atributos[":data-estado"] || "");
  assert.ok(expresiones.some((x) => /\binc\.estado\b/.test(x)), "los estados de conest de las incidencias");
  assert.ok(expresiones.some((x) => /\bfila\.estado\b/.test(x)), "los estados de revisión de la bandeja");
  assert.ok(expresiones.some((x) => /\bp\.estado\b/.test(x)), "los estados de volcado");
});

test("f035 R57: ningún estado se pinta fuera de su chip (salvo las opciones de un filtro)", () => {
  const sueltos = elementos(arbol(leer("index.html"))).filter(
    (e) =>
      e.nombre !== "option" &&
      /\b(etiquetaEstado|estadoVolcado)\(/.test(e.atributos["x-text"] || "") &&
      !(":data-estado" in e.atributos),
  );

  assert.deepEqual(
    sueltos.map((e) => `<${e.nombre} x-text="${e.atributos["x-text"]}">`),
    [],
    "un estado pintado sin chip ni data-estado",
  );
});


// ── Review 4 · Las ligaduras de presentación dicen la verdad del dato ───────
//
// El barrido de la review 4 (una mutación por aparición) dejaba vivas las
// `:class` de presentación: vaciadas, la suite seguía en verde. Aquí se
// EJECUTAN contra el componente y los datos de ejemplo, como lo haría Alpine:
// cada expresión (`x-for`, `x-text`, `:class`, `@click`) se evalúa con el
// componente como ámbito, y se comprueba que la clase cuenta lo mismo que el
// texto que se ve. No se fija la redacción de ninguna expresión.

/** Evalúa una expresión de Alpine con `ambito` como alcance (lo que hace Alpine con `with`). */
function evaluar(expresion, ambito) {
  return new Function("__ambito", `with (__ambito) { return (${expresion}); }`)(ambito);
}

/** Los `x-for` que envuelven a `nodo`, de fuera adentro. */
function buclesDe(nodo) {
  const lista = [];
  for (let n = nodo.padre; n; n = n.padre) {
    if (n.nombre === "template" && n.atributos["x-for"]) lista.unshift(n.atributos["x-for"]);
  }
  return lista;
}

/**
 * El componente con las variables de los `x-for` encima. Es un `Proxy` para
 * que lo que escribe un método (`this.filaBandejaAbierta = id`) caiga en el
 * componente, como en Alpine, y no en una copia.
 */
function ambitoCon(c, variables) {
  return new Proxy(c, {
    has: (destino, clave) => clave in variables || clave in destino,
    get: (destino, clave) => (clave in variables ? variables[clave] : destino[clave]),
    set: (destino, clave, valor) => {
      if (clave in variables) variables[clave] = valor;
      else destino[clave] = valor;
      return true;
    },
  });
}

/** Un ámbito por cada combinación de iteraciones de los `x-for` que envuelven al nodo. */
function ambitosDe(c, nodo, vaciados = false) {
  let combinaciones = [{}];
  for (const bucle of buclesDe(nodo)) {
    const m = bucle.match(/^\s*\(?\s*([\w$]+)\s*(?:,\s*([\w$]+)\s*)?\)?\s+in\s+([\s\S]+)$/);
    assert.ok(m, `x-for sin entender: ${bucle}`);
    const siguientes = [];
    for (const variables of combinaciones) {
      const coleccion = evaluar(m[3], ambitoCon(c, variables));
      Array.from(coleccion || []).forEach((valor, i) => {
        siguientes.push({ ...variables, [m[1]]: valor, ...(m[2] ? { [m[2]]: i } : {}) });
      });
    }
    combinaciones = siguientes;
  }
  if (vaciados) {
    // La misma fila con TODOS sus campos a null: el dato que falta, aunque
    // los datos de ejemplo no traigan ese hueco en ese sitio (todas las
    // incidencias de ejemplo tienen ubicación, por ejemplo).
    const vacio = (v) => (v && typeof v === "object" && !Array.isArray(v)
      ? Object.fromEntries(Object.keys(v).map((k) => [k, null])) : v);
    combinaciones = combinaciones.concat(combinaciones.map((variables) =>
      Object.fromEntries(Object.entries(variables).map(([k, v]) => [k, vacio(v)]))));
  }
  return combinaciones.map((variables) => ambitoCon(c, variables));
}

function clasesEn(nodo, ambito) {
  const fijas = (nodo.atributos.class || "").split(/\s+/);
  const dinamicas = nodo.atributos[":class"] ? String(evaluar(nodo.atributos[":class"], ambito)).split(/\s+/) : [];
  return new Set([...fijas, ...dinamicas].filter(Boolean));
}

/**
 * Estados del componente que abren, a la vez, la fila i de la bandeja, la
 * incidencia i y el capítulo i: así cada panel de detalle se pinta con cada
 * uno de sus datos de ejemplo.
 */
function estadosDeDetalle(c) {
  const d = datos();
  const n = Math.max(d.bandeja.filas.length, d.incidencias.filas.length, d.capitulos.filas.length);
  const estados = [];
  for (let i = 0; i < n; i += 1) {
    estados.push(() => {
      c.filaBandejaAbierta = (d.bandeja.filas[i] || {}).id || null;
      c.incidenciaAbierta = (d.incidencias.filas[i] || {}).id || null;
      c.capituloAbierto = (d.capitulos.filas[i] || {}).obra || null;
    });
  }
  return estados;
}

/** Lo que el portal escribe cuando falta un dato (R22, R25, F-039). */
const SIN_DATO = /^(sin completar|sin enlazar|Sin histórico\b)/;

test("f035 R22/R25: «sin dato» se marca rs-sin-dato, y solo eso (review 4)", () => {
  conVentanaFalsa(() => {
    const c = nuevoComponente();
    const candidatos = elementos(arbol(leer("index.html"))).filter((e) => {
      const x = e.atributos["x-text"] || "";
      return /'sin completar'|'sin enlazar'|Sin histórico|\bimporte\(/.test(x);
    });
    assert.ok(candidatos.length >= 12, `los datos que pueden faltar (hay ${candidatos.length})`);

    const vistos = { conDato: 0, sinDato: 0 };
    const problemas = [];
    for (const fijar of estadosDeDetalle(c)) {
      fijar();
      for (const e of candidatos) {
        // Siempre también con la fila vaciada, y en TODOS los candidatos: los
        // elige su `x-text`, nunca la ligadura que se vigila (review 5: si el
        // vaciado dependiera de tener `:class`, borrar el `:class` lo apagaría).
        for (const ambito of ambitosDe(c, e, true)) {
          const leido = String(evaluar(e.atributos["x-text"], ambito));
          const falta = SIN_DATO.test(leido);
          vistos[falta ? "sinDato" : "conDato"] += 1;
          if (falta !== clasesEn(e, ambito).has("rs-sin-dato")) {
            problemas.push(`<${e.nombre} x-text="${e.atributos["x-text"]}"> dice «${leido}» ${falta ? "sin" : "con"} rs-sin-dato`);
          }
        }
      }
    }
    assert.deepEqual([...new Set(problemas)], [], "la marca rs-sin-dato no cuenta lo mismo que el texto");
    assert.ok(vistos.sinDato > 0 && vistos.conDato > 0, `el test ve los dos casos: ${JSON.stringify(vistos)}`);
  });
});

test("f035 R25: un pendiente del campo se pinta en atención, y solo él (review 4)", () => {
  conVentanaFalsa(() => {
    const c = nuevoComponente();
    const candidatos = elementos(arbol(leer("index.html"))).filter((e) =>
      /'Pendiente: '/.test(e.atributos["x-text"] || ""),
    );
    assert.ok(candidatos.length >= 1, "los orígenes de campo con pendiente");

    const vistos = { pendiente: 0, otro: 0 };
    for (const fijar of estadosDeDetalle(c)) {
      fijar();
      for (const e of candidatos) {
        for (const ambito of ambitosDe(c, e)) {
          const leido = String(evaluar(e.atributos["x-text"], ambito));
          const pendiente = leido.startsWith("Pendiente: ");
          vistos[pendiente ? "pendiente" : "otro"] += 1;
          assert.equal(clasesEn(e, ambito).has("rs-nota--atencion"), pendiente, `«${leido}»: rs-nota--atencion`);
        }
      }
    }
    assert.ok(vistos.pendiente > 0 && vistos.otro > 0, `el test ve los dos casos: ${JSON.stringify(vistos)}`);
  });
});

test("f035 R38/§5.8: la fila abierta, y solo ella, lleva rs-fila--abierta (review 4)", () => {
  conVentanaFalsa(() => {
    const todos = elementos(arbol(leer("index.html")));
    // Toda fila de tabla que se abre con un botón «abrir…» de la propia fila.
    const filas = todos.filter(
      (e) => e.nombre === "tr" && elementos(e).some((b) => /^\s*abrir\w*\(/.test(b.atributos["@click"] || "")),
    );
    assert.ok(filas.length >= 2, `las tablas con detalle (bandeja y capítulos): hay ${filas.length}`);

    for (const tr of filas) {
      const boton = elementos(tr).find((b) => /^\s*abrir\w*\(/.test(b.atributos["@click"] || ""));
      const c = nuevoComponente();
      const ambitos = ambitosDe(c, tr);
      assert.ok(ambitos.length >= 2, `${boton.atributos["@click"]}: al menos dos filas de ejemplo`);
      ambitos.forEach((abierta, k) => {
        evaluar(boton.atributos["@click"], abierta);
        const marcadas = ambitos.map((ambito) => clasesEn(tr, ambito).has("rs-fila--abierta"));
        assert.deepEqual(
          marcadas,
          ambitos.map((_, j) => j === k),
          `${boton.atributos["@click"]}: tras abrir la fila ${k}, solo ella va marcada`,
        );
      });
    }
  });
});

test("f035 R11: el aviso de un placeholder se ve en su tarjeta, y sin aviso no hay tarjeta (review 4)", () => {
  conVentanaFalsa(() => {
    const c = nuevoComponente();
    const region = elementos(arbol(leer("index.html"))).find(
      (e) => e.atributos.role === "status" && (e.atributos["x-text"] || "").trim() === "aviso",
    );
    assert.ok(region, "la región role=\"status\" del aviso (R11)");
    const tarjeta = region.padre;

    assert.equal(clasesEn(tarjeta, c).has("rs-toast--visible"), false, "sin aviso, sin tarjeta");
    c.placeholder(portal().PLACEHOLDERS[0].id);
    assert.ok(c.aviso, "el placeholder deja su aviso");
    assert.equal(clasesEn(tarjeta, c).has("rs-toast--visible"), true, "con aviso, en su tarjeta");
  });
});
