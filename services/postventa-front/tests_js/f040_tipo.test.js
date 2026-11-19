// services/postventa-front/tests_js/f040_tipo.test.js
// F-040 R63–R67 · Bloque 1 bis: el tipo de reclamación de F-072 en el panel de
// volcado y los textos de su Q-11 en la revisión.
//
// `specs/F-040-volcado-sigrid/requirements.md` §1.2 y `design.md` §3.1, §3.4 y
// §7. Lo que se fija, además de lo obvio:
//
// - R63: el tipo del ensayo sale con la etiqueta de `catalogo.listados`; un
//   código que no está en la lista, tal cual; `TEXTO_TIPO` ya no existe.
// - R64 [D-2]: el recuento por tipo solo aparece con más de un tipo entre los
//   `previsto`; con uno solo, el texto de la confirmación no cambia.
// - R65, R66 [D-1]: los textos de `tipo_no_valido` y `tipo_fuera_de_sigrid`, y
//   los diez motivos en su orden.
// - R67 [D-3]: `opcionesDeListado` sin opción en blanco y con la del tipo no
//   vigente; el historial nunca dice «sin listado».
//
// Todo inventado: obra 9901, unidades 9901-0N «VILLA 9N», oficio OF01,
// proveedor EJ11, tipos 0002/0003 con etiquetas de ejemplo y 9001 desconocido.
// Ningún test abre red.

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const Volcado = require("../js/volcado.js");
const Revision = require("../js/revision.js");

const OBRA = "9901";
const ID = (n) => "00000000-0000-4000-8000-" + String(n).padStart(12, "0");

const ETIQUETA_0002 = "PRIMER LISTADO EJEMPLO (0002)";
const ETIQUETA_0003 = "POST VENTA EJEMPLO (0003)";

function catalogo() {
  return {
    unidades: [
      { codigo: "9901-01", nombre: "VILLA 91" },
      { codigo: "9901-02", nombre: "VILLA 92" },
    ],
    ubicaciones: {},
    oficios: [{ codigo: "OF01", nombre: "FONTANERIA DE EJEMPLO", grupo: null }],
    pares: [{ oficio_codigo: "OF01", proveedor_codigo: "EJ11", proveedor_nombre: "PROVEEDOR EJEMPLO 11" }],
    urgencias: [],
    listados: [
      { codigo: "0002", etiqueta: ETIQUETA_0002 },
      { codigo: "0003", etiqueta: ETIQUETA_0003 },
    ],
  };
}

function parte(n, estado, tipo, extra) {
  const id = ID(n);
  return Object.assign(
    {
      incidencia_id: id,
      revision_id: ID(200 + n),
      referencia_externa: "PVI-" + id,
      estado: estado,
      motivo: null,
      sigrid_cod: null,
      envio: {
        referencia_externa: "PVI-" + id,
        unidad_postventa: n % 2 ? "9901-01" : "9901-02",
        descripcion: "Descripción de ejemplo " + n,
        tipo: tipo,
        oficio: "OF01",
        ubicacion: "COCINA",
        forma_comunicacion: "E",
        intervinientes: [{ oficio: "OF01", proveedor: "EJ11", causante: false }],
      },
    },
    extra || {},
  );
}

function ensayo(partes) {
  return {
    ensayo_id: "ensayo-de-ejemplo",
    caduca_at_utc: "2026-11-19T10:30:00Z",
    resumen: {},
    partes: partes,
    excluidas: [],
    sigrid: null,
  };
}

// --- R63 · el tipo con la etiqueta de catalogo.listados -------------------------------------

test("f040 R63: el tipo de cada parte del ensayo sale con su etiqueta de catalogo.listados", () => {
  const vista = Volcado.juntarEnsayos(
    [ensayo([parte(1, "previsto", "0002"), parte(2, "previsto", "0003"), parte(3, "idempotente", "0003")])],
    catalogo(),
  );
  assert.deepEqual(vista.filas.map((f) => f.tipo), [ETIQUETA_0002, ETIQUETA_0003, ETIQUETA_0003]);
});

test("f040 R63: un tipo que no está en catalogo.listados (de baja o desconocido) sale con su código tal cual", () => {
  const vista = Volcado.juntarEnsayos([ensayo([parte(1, "rechazado", "9001", { motivo: "tipo_no_valido" })])], catalogo());
  assert.equal(vista.filas[0].tipo, "9001");
  const sinCatalogo = Volcado.juntarEnsayos([ensayo([parte(1, "previsto", "0002")])], null);
  assert.equal(sinCatalogo.filas[0].tipo, "0002", "sin catálogo, el código: nunca un nombre inventado");
  const sinListados = Volcado.juntarEnsayos([ensayo([parte(1, "previsto", "0002")])], Object.assign(catalogo(), { listados: undefined }));
  assert.equal(sinListados.filas[0].tipo, "0002");
  const etiquetaVacia = catalogo();
  etiquetaVacia.listados[0].etiqueta = "";
  assert.equal(Volcado.juntarEnsayos([ensayo([parte(1, "previsto", "0002")])], etiquetaVacia).filas[0].tipo, "0002");
});

test("f040 R63: la tabla fija TEXTO_TIPO (Q-1, «siempre 0002») ya no existe", () => {
  const fuente = fs.readFileSync(path.join(__dirname, "..", "js", "volcado.js"), "utf8");
  assert.equal(Volcado.TEXTO_TIPO, undefined);
  assert.doesNotMatch(fuente, /TEXTO_TIPO/);
  assert.doesNotMatch(fuente, /PRIMER LISTADO POSTVENTA/, "ninguna etiqueta de tipo escrita a mano en el panel");
});

// --- R64 [D-2] · el recuento por tipo ------------------------------------------------------

test("f040 R64: recuentoPorTipo cuenta por tipo, en el orden de aparición, con su etiqueta (o el código)", () => {
  const filas = [
    { tipo_codigo: "0003" },
    { tipo_codigo: "0002" },
    { tipo_codigo: "0003" },
    { tipo_codigo: "9001" },
  ];
  assert.deepEqual(Volcado.recuentoPorTipo(filas, catalogo()), [
    { tipo_codigo: "0003", etiqueta: ETIQUETA_0003, n: 2 },
    { tipo_codigo: "0002", etiqueta: ETIQUETA_0002, n: 1 },
    { tipo_codigo: "9001", etiqueta: "9001", n: 1 },
  ]);
  assert.deepEqual(Volcado.recuentoPorTipo([], catalogo()), []);
  assert.deepEqual(Volcado.recuentoPorTipo(null, catalogo()), []);
});

test("f040 R64: juntarEnsayos cuenta por tipo solo lo que se crearía (los previsto)", () => {
  const vista = Volcado.juntarEnsayos(
    [
      ensayo([parte(1, "previsto", "0002"), parte(2, "previsto", "0003"), parte(3, "previsto", "0002")]),
      ensayo([parte(4, "idempotente", "0003"), parte(5, "rechazado", "9001", { motivo: "tipo_no_valido" })]),
    ],
    catalogo(),
  );
  assert.deepEqual(vista.porTipo, [
    { tipo_codigo: "0002", etiqueta: ETIQUETA_0002, n: 2 },
    { tipo_codigo: "0003", etiqueta: ETIQUETA_0003, n: 1 },
  ]);
  assert.equal(vista.filas[0].tipo_codigo, "0002");
});

const POR_UNIDAD = [
  { unidad_codigo: "9901-01", nombre: "VILLA 91", n: 2 },
  { unidad_codigo: "9901-02", nombre: "VILLA 92", n: 1 },
];

test("f040 R64: con un solo tipo, el texto de la confirmación no cambia", () => {
  const sin = Volcado.textoConfirmacion(3, POR_UNIDAD, OBRA);
  assert.equal(sin, "Se van a crear 3 partes en el ERP de producción de la obra 9901: 2 de VILLA 91 y 1 de VILLA 92. Escribe 3 para confirmar.");
  assert.equal(Volcado.textoConfirmacion(3, POR_UNIDAD, OBRA, [{ tipo_codigo: "0003", etiqueta: ETIQUETA_0003, n: 3 }]), sin);
  assert.equal(Volcado.textoConfirmacion(3, POR_UNIDAD, OBRA, []), sin);
});

test("f040 R64: con dos tipos, la confirmación dice además el recuento por tipo con su etiqueta", () => {
  const texto = Volcado.textoConfirmacion(3, POR_UNIDAD, OBRA, [
    { tipo_codigo: "0002", etiqueta: ETIQUETA_0002, n: 2 },
    { tipo_codigo: "0003", etiqueta: ETIQUETA_0003, n: 1 },
  ]);
  assert.equal(
    texto,
    "Se van a crear 3 partes en el ERP de producción de la obra 9901: 2 de VILLA 91 y 1 de VILLA 92; por tipo, 2 " +
      ETIQUETA_0002 + " y 1 " + ETIQUETA_0003 + ". Escribe 3 para confirmar.",
  );
});

test("f040 R64: textoPorTipo (el resumen del ensayo) es vacío con un tipo o ninguno y dice el recuento con dos o más", () => {
  assert.equal(Volcado.textoPorTipo([]), "");
  assert.equal(Volcado.textoPorTipo(null), "");
  assert.equal(Volcado.textoPorTipo([{ tipo_codigo: "0002", etiqueta: ETIQUETA_0002, n: 4 }]), "");
  assert.equal(
    Volcado.textoPorTipo([
      { tipo_codigo: "0002", etiqueta: ETIQUETA_0002, n: 2 },
      { tipo_codigo: "0003", etiqueta: ETIQUETA_0003, n: 1 },
      { tipo_codigo: "9001", etiqueta: "9001", n: 1 },
    ]),
    "Por tipo: 2 " + ETIQUETA_0002 + ", 1 " + ETIQUETA_0003 + " y 1 9001",
  );
});

test("f040 R64: el componente pasa el recuento por tipo a la confirmación y al resumen del ensayo", () => {
  const app = Volcado.conPanel({ catalogo: catalogo() }, { api: {} });
  app.volcado = Volcado.estadoInicial(OBRA);
  app.volcado.vistaEnsayo = Volcado.juntarEnsayos(
    [ensayo([parte(1, "previsto", "0002"), parte(2, "previsto", "0003"), parte(3, "previsto", "0002")])],
    catalogo(),
  );
  assert.match(app.volcadoConfirmacion(), /; por tipo, 2 PRIMER LISTADO EJEMPLO \(0002\) y 1 POST VENTA EJEMPLO \(0003\)\. Escribe 3/);
  assert.equal(app.volcadoPorTipo(), "Por tipo: 2 " + ETIQUETA_0002 + " y 1 " + ETIQUETA_0003);

  app.volcado.vistaEnsayo = Volcado.juntarEnsayos([ensayo([parte(1, "previsto", "0003")])], catalogo());
  assert.doesNotMatch(app.volcadoConfirmacion(), /por tipo/);
  assert.equal(app.volcadoPorTipo(), "");
  app.volcado.vistaEnsayo = null;
  assert.equal(app.volcadoPorTipo(), "");
});

// --- R65 [D-1] · tipo_no_valido ------------------------------------------------------------

const TEXTO_TIPO_NO_VALIDO =
  "El tipo de reclamación no existe o está de baja en Sigrid: cambia el tipo en la revisión y vuelve a aprobarla";

test("f040 R65: tipo_no_valido tiene el texto que dice qué hacer, en TEXTO_MOTIVO_VOLCADO de revision.js", () => {
  assert.equal(Revision.textoMotivoVolcado("tipo_no_valido"), TEXTO_TIPO_NO_VALIDO);
});

test("f040 R65: un rechazado por tipo_no_valido sale «No se crea» con su texto y no cuenta en N", () => {
  const vista = Volcado.juntarEnsayos(
    [ensayo([parte(1, "previsto", "0002"), parte(2, "rechazado", "9001", { motivo: "tipo_no_valido" })])],
    catalogo(),
  );
  assert.deepEqual([vista.filas[1].etiqueta, vista.filas[1].motivo], ["No se crea", TEXTO_TIPO_NO_VALIDO]);
  assert.equal(vista.n, 1);
  assert.deepEqual(vista.porTipo.map((t) => t.tipo_codigo), ["0002"]);
});

// --- R66 [D-1] · tipo_fuera_de_sigrid y los diez motivos --------------------------------------

test("f040 R66: diez motivos, con tipo_fuera_de_sigrid entre proveedor_ambiguo y duplicada, y su texto", () => {
  assert.equal(Revision.MOTIVOS.length, 10);
  const i = Revision.MOTIVOS.indexOf("tipo_fuera_de_sigrid");
  assert.equal(Revision.MOTIVOS[i - 1], "proveedor_ambiguo");
  assert.equal(Revision.MOTIVOS[i + 1], "duplicada");
  assert.equal(Revision.textoMotivo("tipo_fuera_de_sigrid"), "El tipo de reclamación ya no está vigente en Sigrid: elige otro");
});

test("f040 R66: el resumen cuenta diez motivos, con tipo_fuera_de_sigrid en su sitio y no al final como desconocido", () => {
  const vista = Revision.presentarResumen({
    total: 3,
    con_motivos: 1,
    por_estado: { nueva: 3 },
    por_motivo: { tipo_fuera_de_sigrid: 1 },
  });
  assert.equal(vista.porMotivo.length, 10);
  const fila = vista.porMotivo[8];
  assert.deepEqual([fila.motivo, fila.texto, fila.n], ["tipo_fuera_de_sigrid", "El tipo de reclamación ya no está vigente en Sigrid: elige otro", 1]);
  assert.equal(vista.porMotivo[9].motivo, "duplicada");
});

// --- R67 [D-3] · el campo «Listado (tipo de reclamación)» y el historial ------------------------

test("f040 R67: opcionesDeListado con el tipo actual vigente: los de catalogo.listados, sin opción en blanco", () => {
  assert.deepEqual(Revision.opcionesDeListado(catalogo(), "0003"), [
    { codigo: "0002", etiqueta: ETIQUETA_0002, fueraDeLista: false },
    { codigo: "0003", etiqueta: ETIQUETA_0003, fueraDeLista: false },
  ]);
  for (const opciones of [Revision.opcionesDeListado(catalogo(), "0002"), Revision.opcionesDeListado(catalogo(), null)]) {
    assert.ok(opciones.every((o) => o.codigo), "ninguna opción en blanco");
  }
});

test("f040 R67: opcionesDeListado con un tipo de baja añade una opción más con su código y «(ya no vigente en Sigrid)»", () => {
  assert.deepEqual(Revision.opcionesDeListado(catalogo(), "9001"), [
    { codigo: "0002", etiqueta: ETIQUETA_0002, fueraDeLista: false },
    { codigo: "0003", etiqueta: ETIQUETA_0003, fueraDeLista: false },
    { codigo: "9001", etiqueta: "9001 (ya no vigente en Sigrid)", fueraDeLista: true },
  ]);
  assert.deepEqual(Revision.opcionesDeListado(catalogo(), ""), Revision.opcionesDeListado(catalogo(), "0002"));
  assert.deepEqual(Revision.opcionesDeListado(null, "9001"), [
    { codigo: "9001", etiqueta: "9001 (ya no vigente en Sigrid)", fueraDeLista: true },
  ]);
});

test("f040 R67: el formulario de la revisión ofrece opcionesDeListado del tipo de la incidencia", () => {
  const app = Revision.crearAppRevision({ api: {}, parametros: "" });
  app.catalogo = catalogo();
  app.formulario = Revision.formularioDe({ unidad_codigo: "9901-01", listado: "9001" }, catalogo());
  assert.deepEqual(app.opciones().listados, Revision.opcionesDeListado(catalogo(), "9001"));
  app.formulario.listado = "0002";
  assert.deepEqual(
    app.opciones().listados.map((o) => o.codigo),
    ["0002", "0003", "9001"],
    "la opción del no vigente sigue mientras sea el tipo guardado, aunque se elija otro",
  );
});

test("f040 R67: en el detalle y el historial, el listado sale con su etiqueta o su código, nunca «sin listado»", () => {
  function listadoDe(vigente, importado) {
    const detalle = Revision.detalleDe(
      { vigentes: { listado: vigente }, importados: { listado: importado }, cambios: ["listado"] },
      catalogo(),
    );
    return detalle.find((c) => c.campo === "listado");
  }
  const conEtiqueta = listadoDe("0003", "0002");
  assert.equal(conEtiqueta.valor, ETIQUETA_0003);
  assert.equal(conEtiqueta.llegoAsi, "llegó así: " + ETIQUETA_0002);
  assert.equal(listadoDe("9001", null).valor, "9001");
  const nulo = listadoDe(null, null);
  assert.doesNotMatch(nulo.valor + " " + nulo.llegoAsi, /sin listado/);
});
