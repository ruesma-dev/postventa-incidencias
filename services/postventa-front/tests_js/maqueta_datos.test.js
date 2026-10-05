// services/postventa-front/tests_js/maqueta_datos.test.js
// F-035 · R21-R26 y R38-R41 · Los datos de ejemplo de la maqueta del portal.
//
// `js/maqueta_datos.js` es **solo datos**: el fixture del que se pintan todas
// las secciones del portal (`design.md` §7). Estos tests son la única defensa
// de dos cosas que la maqueta promete a Posventa:
//
// - que **ningún dato es de nadie** (R24): obras `99NN`, partes `RS99…`,
//   correos en `ejemplo.invalid`, personas y empresas «Ejemplo», ni un DNI ni
//   un teléfono. Los **catálogos generales** de Sigrid —estados, tipos de
//   reclamación, formas de comunicación, oficios— van con sus códigos reales
//   (decisión D-10): no son datos de nadie y son lo que Posventa reconoce.
// - que lo que enseña **cuadra con el contrato** que imita: los campos del
//   alta de `docs/referencia/04_alta_incidencia_sigrid.md` (R38, R39) y los
//   estados y motivos de `sigrid/partes-reclamacion` (`azure-apps/
//   sigrid_api.md` §8.9, R40), sin llamar a nada.
//
// Forma de los datos que fijan estos tests (el diseño da los bloques y los
// nombres de los campos del alta; lo que no nombra, lo fija aquí):
//
//   obras.filas[]         {cod: "99NN", res: "… EJEMPLO …"}
//   bandeja.filas[]       {id, origen, estado, obra, …campos del alta}
//   incidencias.filas[]   {id: "EJ-NNNN", cod: "RS99.NN/NNNN", obra, estado,
//                          …campos del alta, carpetaArchivo?}
//   campos del alta       unidad {cod, res}, descripcionCorta,
//                         descripcionLarga, ubicacion, oficio (código),
//                         tipo (código), forma (código), propietario
//                         {cod, res}, persona {cod, res}, intervinientes
//                         [{oficio, proveedor {cod, res}, causante}],
//                         referenciaExterna
//   propuestas.oficiosObra {"<obra>": [{oficio, proveedor {cod, res},
//                          comentario}]}
//   volcado.catalogos     tipos/formas/oficios [{cod, res}], estados
//                         [{cod, etiqueta}], motivos ["<código>"]
//   volcado.dryRun/hecho  {obra, partes: [{referenciaExterna, unidad
//                          {cod, res}, estado, cod, provisional, motivo
//                          {codigo, mensaje} | null}]}
//   *.pendientes[]        "Pendiente: <qué falta>"
//
// El módulo se carga DENTRO de cada test y no en la cabecera: en la fase RED
// no existe, y un `require` de cabecera tumbaría el fichero entero con un solo
// error sin nombre de requisito.

const test = require("node:test");
const assert = require("node:assert/strict");

function datos() {
  return require("../js/maqueta_datos.js");
}

/** Recorre cualquier valor y llama a `visita(valor, ruta)` en cada nodo. */
function recorrer(valor, visita, ruta) {
  const aqui = ruta || "MaquetaDatos";
  visita(valor, aqui);
  if (valor && typeof valor === "object") {
    for (const clave of Object.keys(valor)) {
      recorrer(valor[clave], visita, `${aqui}.${clave}`);
    }
  }
}

/** Todas las cadenas del fixture, con la ruta donde viven. */
function cadenas(raiz) {
  const encontradas = [];
  recorrer(raiz, (valor, ruta) => {
    if (typeof valor === "string") encontradas.push({ valor, ruta });
  });
  return encontradas;
}

function filasConAlta(d) {
  return [
    ...d.bandeja.filas.map((fila) => ({ fila, donde: `bandeja ${fila.id}` })),
    ...d.incidencias.filas.map((fila) => ({ fila, donde: `incidencia ${fila.id}` })),
  ];
}

function codigos(catalogo) {
  return new Set(catalogo.map((entrada) => String(entrada.cod)));
}

//: Bloques de `design.md` §7.1 y la ficha que retira cada uno (R23, R28). El
//: de `entrada` (F-036) se retiró en la enmienda del 2026-10-05: F-036 está done.
const BLOQUES = {
  obras: "F-041",
  web: "F-037",
  bandeja: "F-038",
  propuestas: "F-039",
  incidencias: "F-041",
  noProcede: "F-042",
  impresion: "F-044",
  capitulos: "F-046",
  vinculos: "F-047",
  datamart: "F-048",
  volcado: "F-040",
};

//: Campos del alta que trae cada fila (R38) y los únicos que admiten `null`:
//: los que la bandeja completa (F-036 los deja opcionales, F-038 los rellena).
const CAMPOS_ALTA = [
  "unidad",
  "descripcionCorta",
  "descripcionLarga",
  "ubicacion",
  "oficio",
  "tipo",
  "forma",
  "propietario",
  "persona",
  "intervinientes",
  "referenciaExterna",
];
const ADMITEN_NULL = new Set(["ubicacion", "oficio", "intervinientes"]);

//: Estados de `conest` para partes de reclamación (R21), por código.
const ESTADOS_CONEST = ["SAT", "PTE", "TER", "NPR", "CER"];

//: Estados por parte del contrato de `sigrid/partes-reclamacion` y su
//: etiqueta legible (`design.md` §5.3, R40).
const ETIQUETAS_VOLCADO = {
  previsto: "Se crearía",
  creado: "Creado en Sigrid",
  idempotente: "Ya estaba creado: no se duplica",
  rechazado: "No se crea: hay que corregirlo",
  no_procesado: "No se llegó a intentar: se puede reenviar",
};

//: Lista cerrada de códigos de parte del contrato (`sigrid_api.md` §8.9).
const MOTIVOS_CONTRATO = [
  "referencia_no_permitida",
  "referencia_duplicada_en_lote",
  "referencia_en_conflicto",
  "unidad_postventa_no_encontrada",
  "tipo_no_valido",
  "clase_no_valida",
  "oficio_no_esta_en_la_obra",
  "interviniente_no_esta_en_la_obra",
  "interviniente_ambiguo",
  "interviniente_repetido",
  "numeracion_agotada",
  "colision_de_clave",
  "filas_afectadas_inesperadas",
  "error_de_escritura",
  "presupuesto_de_tiempo_agotado",
];

//: Oficios del catálogo general de Sigrid que cita el alta manual
//: (`04_alta_incidencia_sigrid.md` §3 y §4), con su resumen real (D-10).
const OFICIOS_DEL_ALTA = {
  "0005": "Carpintería PVC",
  "0011": "Electricidad",
  "0021": "Impermeabilizaciones",
  "0024": "Jardinería",
  "0143": "Carpintería de madera",
};

//: Orígenes admitidos para los campos de la ficha (R25): la lista cerrada de
//: `design.md` §5.5 con su enmienda del 2026-09-25.
const ORIGENES = new Set([
  "con.cod",
  "con.res",
  "conest.cod",
  "rcp.fec",
  "rcp.hor",
  "rcp.upvide",
  "upv.obride",
  "rcp.cliide",
  "rcp.recide",
  "rcp.cntide",
  "rcp.tel",
  "rcp.ele",
  "rcp.tex",
  "rcp.rcpide",
  "rcp.trcpide",
  "rcp.motrcp",
  "rcp.rcptip",
  "rcp.fecpre",
  "rcp.solrcp",
  "rcp.resubi",
  "rcp.texurg",
  "rcp.ofcide",
  "rcpint.obrofcide",
  "rcpint.cauave",
  "upv.fecfin1",
  "upv.fecini2",
  "upv.fecfin2",
  "upv.fecini3",
  "upv.fecesc",
  "upv.fecvtec",
  "obrofc.ofcide",
  "obrofc.prvide",
  "conext[RCPCLI]",
  "propio",
  "pendiente",
]);

// ── R23 · Un único sitio, por bloques, cada uno con su ficha ───────────────

test("f035 R23: los datos de ejemplo están en bloques y cada uno declara la ficha que lo sustituirá", () => {
  const d = datos();

  for (const [bloque, ficha] of Object.entries(BLOQUES)) {
    assert.ok(d[bloque], `falta el bloque ${bloque} en MaquetaDatos`);
    assert.equal(d[bloque].ficha, ficha, `el bloque ${bloque} es de ${ficha}`);
  }
  for (const [bloque, contenido] of Object.entries(d)) {
    assert.match(
      String(contenido && contenido.ficha),
      /^F-0\d\d$/,
      `el bloque ${bloque} no declara su ficha con la forma F-0NN`,
    );
    assert.notEqual(
      contenido.ficha,
      "F-035",
      `el bloque ${bloque} no puede ser de F-035: quedaría vivo para siempre (R28)`,
    );
  }
});

test("f035 R23: MaquetaDatos está congelado entero y no lleva ni una función", () => {
  const d = datos();

  recorrer(d, (valor, ruta) => {
    assert.notEqual(typeof valor, "function", `${ruta} es una función: el fichero es solo datos`);
    if (valor && typeof valor === "object") {
      assert.ok(Object.isFrozen(valor), `${ruta} no está congelado (Object.freeze profundo)`);
    }
  });
});

// ── R24 · Evidentemente ficticios ──────────────────────────────────────────

test("f035 R24: las obras son 99NN con nombre de ejemplo, y toda obra citada existe", () => {
  const d = datos();
  const obras = d.obras.filas;

  assert.ok(obras.length >= 2, "hacen falta al menos dos obras para enseñar el volcado por obra");
  for (const obra of obras) {
    assert.match(obra.cod, /^99\d\d$/, `obra ${obra.cod}: el código de ejemplo es 99NN`);
    assert.match(obra.res, /ejemplo/i, `obra ${obra.cod}: el nombre tiene que decir «Ejemplo»`);
  }

  const conocidas = new Set(obras.map((obra) => obra.cod));
  for (const { fila, donde } of filasConAlta(d)) {
    assert.ok(conocidas.has(fila.obra), `${donde}: la obra ${fila.obra} no está en obras.filas`);
  }
  assert.ok(conocidas.has(d.volcado.dryRun.obra), "la obra del dry-run no está en obras.filas");
  assert.ok(conocidas.has(d.volcado.hecho.obra), "la obra del volcado hecho no está en obras.filas");
});

test("f035 R24: las incidencias son RS99.NN/NNNN con identificador de ruta EJ-NNNN", () => {
  const d = datos();
  const ids = d.incidencias.filas.map((fila) => fila.id);

  assert.ok(ids.length > 0, "no hay incidencias de ejemplo");
  assert.equal(new Set(ids).size, ids.length, "hay identificadores de incidencia repetidos");
  for (const fila of d.incidencias.filas) {
    assert.match(fila.id, /^EJ-\d{4}$/, `${fila.id}: el identificador de ruta es EJ-NNNN`);
    assert.match(fila.cod, /^RS99\.\d\d\/\d{4}$/, `${fila.id}: el código es RS99.NN/NNNN`);
  }
});

test("f035 R24: unidades, propietarios, personas y referencias cuelgan de su obra 99NN", () => {
  const d = datos();

  for (const { fila, donde } of filasConAlta(d)) {
    const obra = fila.obra;
    assert.match(
      fila.unidad.cod,
      new RegExp(`^${obra}\\.03VILLA \\d+\\.$`),
      `${donde}: la unidad de posventa es ${obra}.03VILLA N.`,
    );
    assert.match(fila.unidad.res, /ejemplo/i, `${donde}: el resumen de la unidad dice «ejemplo»`);
    assert.match(
      fila.propietario.cod,
      new RegExp(`^${obra}_REF/\\d{4}$`),
      `${donde}: el propietario es ${obra}_REF/NNNN`,
    );
    assert.match(fila.propietario.res, /Ejemplo/, `${donde}: el propietario se llama «… Ejemplo …»`);
    assert.match(
      fila.persona.cod,
      new RegExp(`^${obra}_PER/\\d{4}$`),
      `${donde}: la persona que reclama es ${obra}_PER/NNNN`,
    );
    assert.match(fila.persona.res, /Ejemplo/, `${donde}: la persona se llama «… Ejemplo …»`);
    assert.match(
      fila.referenciaExterna,
      /^PVI-EJEMPLO-\d{4}$/,
      `${donde}: la referencia externa es PVI-EJEMPLO-NNNN`,
    );
  }
});

test("f035 R24: los proveedores son EJNN con nombre de ejemplo", () => {
  const d = datos();
  const proveedores = [];
  for (const { fila } of filasConAlta(d)) {
    for (const interviniente of fila.intervinientes || []) proveedores.push(interviniente.proveedor);
  }
  for (const lista of Object.values(d.propuestas.oficiosObra)) {
    for (const oficio of lista) proveedores.push(oficio.proveedor);
  }

  assert.ok(proveedores.length > 0, "no hay ni un proveedor de ejemplo");
  for (const proveedor of proveedores) {
    assert.match(proveedor.cod, /^EJ\d\d$/, `proveedor ${proveedor.cod}: el código es EJNN`);
    assert.match(proveedor.res, /Ejemplo/, `proveedor ${proveedor.cod}: el nombre dice «Ejemplo»`);
  }
});

test("f035 R24: ni un DNI, NIE, NIF, teléfono, URL ni correo fuera de ejemplo.invalid", () => {
  const d = datos();
  const reglas = [
    [/\b\d{8}[A-Z]\b/, "algo con forma de DNI"],
    [/\b[XYZ]\d{7}[A-Z]\b/, "algo con forma de NIE"],
    [/\b[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]\b/, "algo con forma de NIF de empresa"],
    [/(?:\+34\s?)?\b[6789]\d{2}[\s.]?\d{3}[\s.]?\d{3}\b/, "algo con forma de teléfono"],
    [/:\/\//, "una URL"],
    [/sharepoint/i, "una referencia a SharePoint"],
  ];

  for (const { valor, ruta } of cadenas(d)) {
    for (const [patron, que] of reglas) {
      assert.doesNotMatch(valor, patron, `${ruta} contiene ${que}: «${valor}»`);
    }
    for (const correo of valor.match(/[^\s@<>"]+@[^\s@<>"]+/g) || []) {
      assert.match(correo, /@ejemplo\.invalid$/, `${ruta}: el correo ${correo} no es del dominio reservado`);
    }
    for (const codigo of valor.match(/\bRS\d\d\.\d\d\/\d{4}\b/g) || []) {
      assert.match(codigo, /^RS99\./, `${ruta}: ${codigo} parece un parte real (los de ejemplo son RS99…)`);
    }
    for (const referencia of valor.match(/\bPVI-[A-Z0-9-]+/g) || []) {
      assert.match(referencia, /^PVI-EJEMPLO-\d{4}$/, `${ruta}: ${referencia} no es una referencia de ejemplo`);
    }
  }
});

// ── R21 y R22 sobre los datos ───────────────────────────────────────────────

test("f035 R21: las incidencias llevan el estado por código de conest, y salen los cinco", () => {
  const d = datos();
  const usados = new Set();

  for (const fila of d.incidencias.filas) {
    assert.equal(typeof fila.estado, "string", `${fila.id}: el estado va por código, nunca por número`);
    assert.ok(ESTADOS_CONEST.includes(fila.estado), `${fila.id}: estado desconocido ${fila.estado}`);
    usados.add(fila.estado);
  }
  assert.deepEqual([...usados].sort(), [...ESTADOS_CONEST].sort(), "faltan estados en los datos de ejemplo");
});

test("f035 R22: hay importes enlazados y sin enlazar (null), nunca un cero en lugar de «sin enlazar»", () => {
  const d = datos();
  const vinculos = Object.values(d.vinculos.porIncidencia);
  const ventasCapitulo = d.capitulos.filas.map((fila) => fila.venta);

  assert.ok(vinculos.some((v) => v.venta === null), "falta una incidencia sin enlazar (venta: null)");
  assert.ok(vinculos.some((v) => typeof v.venta === "number"), "falta una incidencia enlazada");
  assert.ok(ventasCapitulo.includes(null), "falta un capítulo con la venta sin enlazar (null)");
  for (const id of Object.keys(d.vinculos.porIncidencia)) {
    assert.ok(
      d.incidencias.filas.some((fila) => fila.id === id),
      `vinculos.porIncidencia cita ${id}, que no es una incidencia de ejemplo`,
    );
  }
});

// ── R25 · Cada campo de la ficha declara su origen ─────────────────────────

test("f035 R25: cada campo de la ficha declara su origen, de la lista cerrada", () => {
  const d = datos();
  const campos = d.incidencias.campos;

  assert.ok(campos.length > 0, "incidencias.campos está vacío");
  const etiquetas = campos.map((campo) => campo.etiqueta);
  assert.equal(new Set(etiquetas).size, etiquetas.length, "hay etiquetas de campo repetidas");

  for (const campo of campos) {
    assert.ok(campo.etiqueta, "un campo sin etiqueta");
    const origenes = Array.isArray(campo.origen) ? campo.origen : [campo.origen];
    assert.ok(origenes.length > 0, `${campo.etiqueta}: sin origen`);
    for (const origen of origenes) {
      assert.ok(ORIGENES.has(origen), `${campo.etiqueta}: el origen «${origen}» no es de la lista cerrada`);
    }
    if (origenes.includes("pendiente")) {
      assert.ok(campo.motivo, `${campo.etiqueta}: un origen «pendiente» lleva su motivo`);
    }
  }
});

// ── R26 · Lo que no ha llegado, como pendiente ─────────────────────────────

test("f035 R26: todo pendiente dice «Pendiente: <qué falta>»", () => {
  const d = datos();
  let cuantos = 0;

  for (const [bloque, contenido] of Object.entries(d)) {
    for (const pendiente of contenido.pendientes || []) {
      cuantos += 1;
      assert.match(pendiente, /^Pendiente: \S/, `${bloque}: «${pendiente}» no empieza por «Pendiente: »`);
    }
  }
  assert.ok(cuantos > 0, "no hay ni un pendiente en los datos de ejemplo");
});

test("f035 R26: están los pendientes mínimos (plantilla, proforma y las dudas del alta)", () => {
  const d = datos();
  const texto = (bloque) => (d[bloque].pendientes || []).join("\n");

  assert.match(texto("impresion"), /plantilla/i, "F-044: falta el pendiente de la plantilla");
  assert.match(texto("vinculos"), /proforma/i, "F-047: falta el pendiente del enlace con la proforma");
  assert.match(texto("volcado"), /0003/, "F-040: falta el pendiente del tipo 0003");
  assert.match(texto("volcado"), /causante/i, "F-040: falta el pendiente de intervinientes y causante");
  assert.match(texto("volcado"), /estado/i, "F-040: falta el pendiente del estado en que nace el parte");
});

// ── R38 · Los campos del alta en cada fila ──────────────────────────────────

test("f035 R38: cada fila de la bandeja y de incidencias trae todos los campos del alta", () => {
  const d = datos();

  for (const { fila, donde } of filasConAlta(d)) {
    for (const campo of CAMPOS_ALTA) {
      assert.ok(campo in fila, `${donde}: falta el campo del alta «${campo}»`);
      if (fila[campo] === null) {
        assert.ok(ADMITEN_NULL.has(campo), `${donde}: «${campo}» no puede ir sin completar`);
      } else {
        assert.notEqual(fila[campo], undefined, `${donde}: «${campo}» es undefined`);
      }
    }
    assert.ok(fila.descripcionCorta.length <= 128, `${donde}: la descripción corta pasa de 128`);
    if (fila.ubicacion !== null) {
      assert.ok(fila.ubicacion.length <= 48, `${donde}: la ubicación pasa de 48`);
    }
    for (const interviniente of fila.intervinientes || []) {
      assert.equal(typeof interviniente.causante, "boolean", `${donde}: «causante» es sí o no`);
    }
  }
});

test("f035 R38: hay al menos una fila de Excel sin ubicación ni oficio, para enseñar «sin completar»", () => {
  const d = datos();

  assert.ok(
    d.bandeja.filas.some((f) => f.origen === "Excel" && f.ubicacion === null && f.oficio === null),
    "falta una fila de Excel con ubicación y oficio sin completar",
  );
});

test("f035 R38: los intervinientes salen de los oficios de la obra con su proveedor", () => {
  const d = datos();
  const oficiosObra = d.propuestas.oficiosObra;

  for (const obra of d.obras.filas) {
    const lista = oficiosObra[obra.cod];
    assert.ok(Array.isArray(lista), `falta propuestas.oficiosObra de la obra ${obra.cod}`);
    assert.ok(lista.length >= 4 && lista.length <= 6, `obra ${obra.cod}: entre 4 y 6 oficios de obra`);
  }
  for (const { fila, donde } of filasConAlta(d)) {
    for (const interviniente of fila.intervinientes || []) {
      const casa = (oficiosObra[fila.obra] || []).some(
        (o) => o.oficio === interviniente.oficio && o.proveedor.cod === interviniente.proveedor.cod,
      );
      assert.ok(
        casa,
        `${donde}: el interviniente ${interviniente.oficio}/${interviniente.proveedor.cod} ` +
          `no es un oficio de la obra ${fila.obra}`,
      );
    }
  }
});

// ── R39 · Tipos y oficios por código de su catálogo ────────────────────────

test("f035 R39: los catálogos del alta llevan los códigos reales de Sigrid (D-10)", () => {
  const { catalogos } = datos().volcado;

  const tipos = Object.fromEntries(catalogos.tipos.map((t) => [String(t.cod), t.res]));
  assert.equal(tipos["0002"], "PRIMER LISTADO POSTVENTA");
  assert.ok("0003" in tipos, "falta el tipo 0003, el que sale por defecto en el escritorio");
  assert.equal(tipos["0003"], null, "el 0003 no tiene resumen: nadie sabe qué es (R39)");

  assert.equal(catalogos.formas.length, 1, "la maqueta solo usa la forma «Escrita»");
  assert.equal(String(catalogos.formas[0].cod), "1");
  assert.equal(catalogos.formas[0].res, "Escrita");

  const oficios = Object.fromEntries(catalogos.oficios.map((o) => [String(o.cod), o.res]));
  for (const [cod, res] of Object.entries(OFICIOS_DEL_ALTA)) {
    assert.equal(oficios[cod], res, `oficio ${cod}: el resumen real es «${res}»`);
  }
});

test("f035 R39: todo tipo, forma y oficio usado en los datos está en su catálogo", () => {
  const d = datos();
  const { catalogos } = d.volcado;
  const tipos = codigos(catalogos.tipos);
  const formas = codigos(catalogos.formas);
  const oficios = codigos(catalogos.oficios);

  for (const { fila, donde } of filasConAlta(d)) {
    assert.ok(tipos.has(String(fila.tipo)), `${donde}: el tipo ${fila.tipo} no está en el catálogo`);
    assert.ok(formas.has(String(fila.forma)), `${donde}: la forma ${fila.forma} no está en el catálogo`);
    if (fila.oficio !== null) {
      assert.ok(oficios.has(String(fila.oficio)), `${donde}: el oficio ${fila.oficio} no está en el catálogo`);
    }
    for (const interviniente of fila.intervinientes || []) {
      assert.ok(
        oficios.has(String(interviniente.oficio)),
        `${donde}: el oficio del interviniente ${interviniente.oficio} no está en el catálogo`,
      );
    }
  }
  for (const [obra, lista] of Object.entries(d.propuestas.oficiosObra)) {
    for (const o of lista) {
      assert.ok(oficios.has(String(o.oficio)), `oficios de la obra ${obra}: ${o.oficio} no está en el catálogo`);
    }
  }
});

test("f035 R39: exactamente una fila de la bandeja usa el tipo 0003, para enseñar su pendiente", () => {
  const d = datos();

  assert.equal(d.bandeja.filas.filter((fila) => String(fila.tipo) === "0003").length, 1);
});

// ── R40 · El panel de volcado, con el contrato de sigrid/partes-reclamacion ─

test("f035 R40: los estados y los motivos son los del contrato, con su etiqueta legible", () => {
  const { catalogos } = datos().volcado;

  const etiquetas = Object.fromEntries(catalogos.estados.map((e) => [e.cod, e.etiqueta]));
  assert.deepEqual(etiquetas, ETIQUETAS_VOLCADO);
  assert.deepEqual([...catalogos.motivos].sort(), [...MOTIVOS_CONTRATO].sort());
});

test("f035 R40: cada resultado es de una sola obra, con referencias PVI- únicas y estados del contrato", () => {
  const { dryRun, hecho, catalogos } = datos().volcado;
  const estados = new Set(catalogos.estados.map((e) => e.cod));

  assert.notEqual(dryRun.obra, hecho.obra, "los dos resultados de ejemplo son de obras distintas");
  for (const [nombre, resultado] of [["dryRun", dryRun], ["hecho", hecho]]) {
    assert.ok(resultado.partes.length > 0, `${nombre}: sin partes`);
    const referencias = resultado.partes.map((p) => p.referenciaExterna);
    assert.equal(new Set(referencias).size, referencias.length, `${nombre}: referencias repetidas`);
    for (const parte of resultado.partes) {
      assert.match(parte.referenciaExterna, /^PVI-/, `${nombre}: la referencia empieza por PVI-`);
      assert.ok(estados.has(parte.estado), `${nombre}: estado ${parte.estado} fuera del contrato`);
      assert.ok(
        parte.unidad.cod.startsWith(`${resultado.obra}.`),
        `${nombre}: la unidad ${parte.unidad.cod} no es de la obra ${resultado.obra} (un lote, una obra)`,
      );
    }
  }
});

test("f035 R40: el dry-run no crea nada y sus códigos previstos son provisionales", () => {
  const { dryRun } = datos().volcado;
  const estados = dryRun.partes.map((p) => p.estado);

  assert.ok(!estados.includes("creado"), "en un dry-run ningún parte está creado");
  for (const esperado of ["previsto", "idempotente", "rechazado"]) {
    assert.ok(estados.includes(esperado), `el dry-run de ejemplo enseña un parte ${esperado}`);
  }
  for (const parte of dryRun.partes) {
    if (parte.estado === "previsto") {
      assert.match(parte.cod, /^RS99\.09\/\d{4}$/, "un previsto lleva el código que tendría");
      assert.equal(parte.provisional, true, "el código de un previsto es provisional (contrato §8.9)");
    } else {
      // Un idempotente ya estaba creado: su código es el de verdad.
      assert.equal(parte.provisional, false, `un ${parte.estado} no lleva código provisional`);
    }
  }
});

test("f035 R40: el volcado hecho no tiene previstos y enseña los cuatro resultados reales", () => {
  const { hecho } = datos().volcado;
  const estados = hecho.partes.map((p) => p.estado);

  assert.ok(!estados.includes("previsto"), "en un volcado hecho ningún parte queda previsto");
  for (const esperado of ["creado", "idempotente", "rechazado", "no_procesado"]) {
    assert.ok(estados.includes(esperado), `el volcado hecho de ejemplo enseña un parte ${esperado}`);
  }
  for (const parte of hecho.partes) {
    assert.equal(parte.provisional, false, "en un volcado hecho ningún código es provisional");
    if (parte.estado === "creado" || parte.estado === "idempotente") {
      assert.match(parte.cod, /^RS99\.09\/\d{4}$/, `un ${parte.estado} lleva su código de Sigrid`);
    }
  }
});

test("f035 R40: rechazados y no procesados llevan motivo de la lista cerrada; los demás, ninguno", () => {
  const { dryRun, hecho, catalogos } = datos().volcado;
  const motivos = new Set(catalogos.motivos);

  for (const parte of [...dryRun.partes, ...hecho.partes]) {
    if (parte.estado === "rechazado" || parte.estado === "no_procesado") {
      assert.ok(parte.motivo, `${parte.referenciaExterna}: un ${parte.estado} dice por qué`);
      assert.ok(motivos.has(parte.motivo.codigo), `${parte.motivo.codigo} no es de la lista cerrada`);
      assert.ok(parte.motivo.mensaje, `${parte.referenciaExterna}: el motivo lleva su mensaje`);
      assert.equal(parte.cod, null, `${parte.referenciaExterna}: sin crear, no hay código de Sigrid`);
    } else {
      assert.equal(parte.motivo, null, `${parte.referenciaExterna}: un ${parte.estado} no lleva motivo`);
    }
    if (parte.estado === "no_procesado") {
      assert.equal(
        parte.motivo.codigo,
        "presupuesto_de_tiempo_agotado",
        "el contrato solo da no_procesado con presupuesto_de_tiempo_agotado",
      );
    }
  }
});

// ── R41 · Dónde está archivado un parte, con la estructura de Posventa ──────

test("f035 R41: la carpeta de archivo es la de Posventa, ficticia, sin fichero ni URL", () => {
  const d = datos();
  const conCarpeta = d.incidencias.filas.filter((fila) => fila.carpetaArchivo);

  assert.ok(conCarpeta.length > 0, "ninguna incidencia de ejemplo enseña dónde está archivado su parte");
  for (const fila of conCarpeta) {
    const carpeta = fila.carpetaArchivo;
    assert.match(
      carpeta,
      /^99\d\d {2}EJEMPLO [^/]+\/PARTES INCIDENCIAS\/VILLA \d{3}\/PARTES FIRMADOS$/,
      `${fila.id}: «${carpeta}» no sigue <obra>  EJEMPLO …/PARTES INCIDENCIAS/VILLA NNN/PARTES FIRMADOS`,
    );
    assert.doesNotMatch(carpeta, /\.pdf/i, `${fila.id}: la carpeta no lleva nombre de fichero`);
    assert.doesNotMatch(carpeta, /:\/\//, `${fila.id}: la carpeta no es una URL`);
    assert.ok(carpeta.startsWith(`${fila.obra}  `), `${fila.id}: la carpeta es de otra obra`);

    const villa = fila.unidad.cod.match(/VILLA (\d+)\.$/);
    assert.ok(villa, `${fila.id}: solo las unidades VILLA enseñan carpeta`);
    assert.ok(
      carpeta.includes(`/VILLA ${villa[1].padStart(3, "0")}/`),
      `${fila.id}: la villa de la carpeta no es la de la unidad (tres cifras, F-049)`,
    );
  }
});
