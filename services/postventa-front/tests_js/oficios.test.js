// services/postventa-front/tests_js/oficios.test.js
// F-036 R80-R82, R86, R88, R89, R98 · La pantalla de oficios repetidos.
//
// Todo inventado: obra 9999, oficios 9001…, «Oficio inventado». La forma de
// las respuestas es la de los handlers (`progress/impl_F-036.md`, B6-18), no
// la tabla de §8 de `design.md`, que todavia escribe una clave `proveedor`.

const test = require("node:test");
const assert = require("node:assert/strict");

const Oficios = require("../js/oficios.js");

/** `GET /api/catalogos/propuestas` inventada: un grupo vigente, dos propuestas y un aviso. */
function respuestaPropuestas() {
  return {
    obra: "9999",
    oficio: {
      oficios: [
        { codigo: "9001", nombre: "Oficio inventado A", grupo: ["9001", "9002"] },
        { codigo: "9002", nombre: "Oficio inventado a", grupo: ["9001", "9002"] },
        { codigo: "9003", nombre: "Pintura inventada", grupo: ["9003"] },
        { codigo: "9004", nombre: "Pinturas inventadas", grupo: ["9004"] },
        { codigo: "9005", nombre: "Pinturas inventada", grupo: ["9005"] },
        { codigo: "9006", nombre: "Carpinteria inventada", grupo: ["9006"] },
        { codigo: "9007", nombre: "Carpinteria inventada de madera", grupo: ["9007"] },
        { codigo: "9008", nombre: null, grupo: ["9008"] },
      ],
      grupos: [
        { etiqueta: "Oficio inventado A", codigos: ["9001", "9002"] },
        { etiqueta: "Pintura inventada", codigos: ["9003"] },
        { etiqueta: "Pinturas inventadas", codigos: ["9004"] },
        { etiqueta: "Pinturas inventada", codigos: ["9005"] },
        { etiqueta: "Carpinteria inventada", codigos: ["9006"] },
        { etiqueta: "Carpinteria inventada de madera", codigos: ["9007"] },
        { etiqueta: "9008", codigos: ["9008"] },
      ],
      propuestas: [
        {
          codigos: ["9003", "9004", "9005"],
          por_pares: false,
          motivos: ["errata", "plural"],
          pares: [
            { codigo_a: "9003", codigo_b: "9004", motivos: ["plural"] },
            { codigo_a: "9003", codigo_b: "9005", motivos: ["errata"] },
            { codigo_a: "9004", codigo_b: "9005", motivos: ["errata"] },
          ],
        },
        {
          codigos: ["9006", "9007"],
          por_pares: false,
          motivos: ["incluido"],
          pares: [{ codigo_a: "9006", codigo_b: "9007", motivos: ["incluido"] }],
        },
      ],
      avisos: [{ codigos: ["9006", "9007", "9099"] }],
    },
  };
}

// --- Motivos legibles (§15.6) ------------------------------------------------

test("f036 R89: los motivos se leen como dice design.md §15.6", () => {
  assert.deepEqual(
    Oficios.motivosLegibles(["mismo_nombre", "plural", "errata", "incluido"]),
    [
      "mismo nombre salvo mayúsculas, tildes o puntuación",
      "plural",
      "posible errata",
      "uno contiene al otro",
    ],
  );
});

test("f036 R89: un motivo desconocido se ensena tal cual, sin romper", () => {
  assert.deepEqual(Oficios.motivosLegibles(["mismo_cif"]), ["mismo_cif"]);
  assert.deepEqual(Oficios.motivosLegibles(undefined), []);
});

// --- Pares ---------------------------------------------------------------------

test("f036 R81: los pares de un grupo, ordenados y sin repetir", () => {
  assert.deepEqual(Oficios.paresDe(["9003", "9001", "9002"]), [
    ["9001", "9002"],
    ["9001", "9003"],
    ["9002", "9003"],
  ]);
  assert.deepEqual(Oficios.paresDe(["9001"]), []);
});

// --- Lo que se pinta (R87, R89, R82) ---------------------------------------------

test("f036 R89: cada propuesta lleva nombres, codigos y motivos legibles", () => {
  const vista = Oficios.presentarPropuestas(respuestaPropuestas());

  assert.equal(vista.obra, "9999");
  assert.equal(vista.propuestas.length, 2);
  const [tres, dos] = vista.propuestas;
  assert.deepEqual(tres.miembros, [
    { codigo: "9003", nombre: "Pintura inventada" },
    { codigo: "9004", nombre: "Pinturas inventadas" },
    { codigo: "9005", nombre: "Pinturas inventada" },
  ]);
  assert.deepEqual(tres.motivos, ["posible errata", "plural"]);
  assert.equal(tres.confirmarEntero, true, "un clique de tres se confirma entero (§15.3)");
  assert.deepEqual(
    tres.pares.map((p) => [p.codigo_a, p.codigo_b, p.nombre_a, p.nombre_b, p.motivos]),
    [
      ["9003", "9004", "Pintura inventada", "Pinturas inventadas", ["plural"]],
      ["9003", "9005", "Pintura inventada", "Pinturas inventada", ["posible errata"]],
      ["9004", "9005", "Pinturas inventadas", "Pinturas inventada", ["posible errata"]],
    ],
  );
  assert.deepEqual(dos.codigos, ["9006", "9007"]);
  assert.equal(typeof tres.clave, "string");
  assert.notEqual(tres.clave, dos.clave);
});

test("f036 R79: una propuesta por pares no se confirma entera", () => {
  const respuesta = respuestaPropuestas();
  respuesta.oficio.propuestas[0].por_pares = true;

  const [porPares] = Oficios.presentarPropuestas(respuesta).propuestas;

  assert.equal(porPares.porPares, true);
  assert.equal(porPares.confirmarEntero, false);
});

test("f036 R89: solo se ensenan los grupos vigentes de mas de un codigo, con sus pares para «Separar»", () => {
  const vista = Oficios.presentarPropuestas(respuestaPropuestas());

  assert.equal(vista.grupos.length, 1);
  assert.equal(vista.grupos[0].etiqueta, "Oficio inventado A");
  assert.deepEqual(vista.grupos[0].miembros, [
    { codigo: "9001", nombre: "Oficio inventado A" },
    { codigo: "9002", nombre: "Oficio inventado a" },
  ]);
  assert.deepEqual(
    vista.grupos[0].pares.map((p) => [p.codigo_a, p.codigo_b]),
    [["9001", "9002"]],
  );
});

test("f036 R84: un codigo del grupo que no es de la obra se ensena sin nombre", () => {
  const vista = Oficios.presentarPropuestas(respuestaPropuestas());

  assert.deepEqual(vista.avisos[0].miembros, [
    { codigo: "9006", nombre: "Carpinteria inventada" },
    { codigo: "9007", nombre: "Carpinteria inventada de madera" },
    { codigo: "9099", nombre: Oficios.SIN_NOMBRE },
  ]);
  assert.match(vista.avisos[0].texto, /no se aplica/);
});

test("f036 R87: un oficio sin nombre en Sigrid se ensena con el marcador", () => {
  assert.equal(Oficios.nombresPorCodigo(respuestaPropuestas().oficio.oficios)["9008"], undefined);
  const vista = Oficios.presentarPropuestas({
    obra: "9999",
    oficio: {
      oficios: [{ codigo: "9008", nombre: null, grupo: ["9008", "9009"] }],
      grupos: [{ etiqueta: "9008", codigos: ["9008", "9009"] }],
      propuestas: [],
      avisos: [],
    },
  });

  assert.deepEqual(vista.grupos[0].miembros.map((m) => m.nombre), [Oficios.SIN_NOMBRE, Oficios.SIN_NOMBRE]);
});

test("f036 R87: una obra sin propuestas, grupos ni avisos lo dice", () => {
  const vacia = Oficios.presentarPropuestas({
    obra: "9999",
    oficio: { oficios: [], grupos: [], propuestas: [], avisos: [] },
  });

  assert.equal(vacia.sinNada, true);
  assert.equal(Oficios.presentarPropuestas(respuestaPropuestas()).sinNada, false);
});

// --- El cuerpo de la decision (R88) ---------------------------------------------

test("f036 R88: el cuerpo lleva confirmado: true booleano y catalogo oficio", () => {
  const cuerpo = Oficios.cuerpoDeDecision("9999", "oid-inventado", ["9004", "9003"], "mismo");

  assert.deepEqual(cuerpo, {
    obra: "9999",
    usuario_oid: "oid-inventado",
    confirmado: true,
    decisiones: [{ catalogo: "oficio", codigos: ["9003", "9004"], decision: "mismo" }],
  });
  assert.equal(cuerpo.confirmado, true);
  assert.equal(typeof cuerpo.confirmado, "boolean");
});

test("f036 R88: una decision que no es «mismo» ni «distinto», o con menos de dos codigos, no se compone", () => {
  assert.throws(() => Oficios.cuerpoDeDecision("9999", "oid", ["9001", "9002"], "Mismo"));
  assert.throws(() => Oficios.cuerpoDeDecision("9999", "oid", ["9001"], "mismo"));
  assert.throws(
    () => Oficios.cuerpoDeDecision("9999", "oid", ["9001", "9002", "9003"], "distinto"),
    /dos/,
    "«distinto» es de dos exactamente (R88)",
  );
});

// --- Los grupos vigentes para la migracion (R98) ----------------------------------

test("f036 R98: el JSON de grupos vigentes lleva solo codigos y solo grupos de mas de uno", () => {
  const datos = Oficios.gruposParaDescargar("9999", [
    { etiqueta: "Pinturas", codigos: ["9005", "9003"] },
    { etiqueta: "Suelto", codigos: ["9008"] },
    { etiqueta: "Oficio A", codigos: ["9002", "9001"] },
  ]);

  assert.deepEqual(datos, {
    obra: "9999",
    oficio: [
      ["9001", "9002"],
      ["9003", "9005"],
    ],
  });
  assert.ok(!JSON.stringify(datos).includes("Pinturas"), "R98: sin nombres");
});

test("f036 R98: el fichero de grupos es un JSON con su nombre", async () => {
  const fichero = Oficios.ficheroDeGrupos("9999", [{ etiqueta: "x", codigos: ["9001", "9002"] }]);

  assert.equal(fichero.nombre, "grupos_vigentes_oficio_9999.json");
  assert.equal(fichero.blob.type, "application/json");
  assert.deepEqual(JSON.parse(await fichero.blob.text()), { obra: "9999", oficio: [["9001", "9002"]] });
});

// --- El componente (con un api doble) -------------------------------------------

function componente(guion) {
  const llamadas = [];
  const respuestas = Object.assign(
    {
      identidad: { usuarioOid: "oid-inventado", correo: "" },
      propuestasCatalogos: respuestaPropuestas(),
      decidirCatalogos: { obra: "9999", pares_guardados: [], grupos_vigentes: { oficio: { grupos: [], avisos: [] } } },
    },
    guion || {},
  );
  const api = {};
  for (const nombre of ["identidad", "propuestasCatalogos", "decidirCatalogos"]) {
    api[nombre] = async (...args) => {
      llamadas.push({ nombre, args });
      const paso = respuestas[nombre];
      if (typeof paso === "function") {
        return paso(...args);
      }
      if (paso instanceof Error) {
        throw paso;
      }
      return paso;
    };
  }
  const guardados = [];
  const app = Oficios.crearAppOficios({
    api,
    guardar: (blob, nombre) => guardados.push({ blob, nombre }),
  });
  return { app, llamadas, guardados };
}

function errorApi(mensaje) {
  const error = new Error(mensaje);
  error.mensaje = mensaje;
  return error;
}

test("f036 R80/R89: cargar las propuestas NO decide nada", async () => {
  const { app, llamadas } = componente();
  await app.iniciar();
  app.obra = " 9999 ";

  await app.cargar();

  assert.deepEqual(llamadas.map((l) => l.nombre), ["identidad", "propuestasCatalogos"]);
  assert.equal(llamadas[1].args[0], "9999");
  assert.equal(app.vista.propuestas.length, 2);
  assert.equal(app.cargando, false);
});

test("f036 R88/R89: confirmado: true solo sale al pulsar, con la obra cargada y el oid", async () => {
  const { app, llamadas } = componente();
  await app.iniciar();
  app.obra = "9999";
  await app.cargar();
  app.obra = "otra-escrita-despues";

  await app.decidir(["9003", "9004", "9005"], "mismo");

  const decisiones = llamadas.filter((l) => l.nombre === "decidirCatalogos");
  assert.equal(decisiones.length, 1);
  assert.deepEqual(decisiones[0].args[0], {
    obra: "9999",
    usuario_oid: "oid-inventado",
    confirmado: true,
    decisiones: [{ catalogo: "oficio", codigos: ["9003", "9004", "9005"], decision: "mismo" }],
  });
  assert.deepEqual(
    llamadas.map((l) => l.nombre),
    ["identidad", "propuestasCatalogos", "decidirCatalogos", "propuestasCatalogos"],
    "cada pulsacion guarda y recarga (§15.6)",
  );
  assert.equal(llamadas[3].args[0], "9999");
  assert.equal(app.decidiendo, false);
});

test("f036 R81: «Separar» guarda «distinto» del par elegido", async () => {
  const { app, llamadas } = componente();
  await app.iniciar();
  app.obra = "9999";
  await app.cargar();

  await app.decidir(["9001", "9002"], "distinto");

  const [decision] = llamadas.filter((l) => l.nombre === "decidirCatalogos");
  assert.deepEqual(decision.args[0].decisiones, [
    { catalogo: "oficio", codigos: ["9001", "9002"], decision: "distinto" },
  ]);
});

test("f036 R89: sin propuestas cargadas o sin usuario no se decide nada", async () => {
  const sinCargar = componente();
  await sinCargar.app.iniciar();
  await sinCargar.app.decidir(["9001", "9002"], "mismo");
  assert.equal(sinCargar.llamadas.filter((l) => l.nombre === "decidirCatalogos").length, 0);

  const sinUsuario = componente({ identidad: { usuarioOid: "", correo: "" } });
  await sinUsuario.app.iniciar();
  sinUsuario.app.obra = "9999";
  await sinUsuario.app.cargar();
  assert.equal(sinUsuario.app.puedeDecidir(), false);
  assert.match(sinUsuario.app.motivoSinDecidir(), /sesión/);
  await sinUsuario.app.decidir(["9001", "9002"], "mismo");
  assert.equal(sinUsuario.llamadas.filter((l) => l.nombre === "decidirCatalogos").length, 0);
});

test("f036 R89: mientras se guarda una decision, no sale otra (ni de un doble clic)", async () => {
  let soltar = null;
  const { app, llamadas } = componente({
    decidirCatalogos: () => new Promise((resolver) => { soltar = () => resolver({}); }),
  });
  await app.iniciar();
  app.obra = "9999";
  await app.cargar();

  const primera = app.decidir(["9001", "9002"], "distinto");
  assert.equal(app.puedeDecidir(), false);
  await app.decidir(["9001", "9002"], "distinto");
  soltar();
  await primera;

  assert.equal(llamadas.filter((l) => l.nombre === "decidirCatalogos").length, 1);
});

test("f036 R52: un 409 al decidir ensena el motivo y no recarga", async () => {
  const { app, llamadas } = componente({ decidirCatalogos: errorApi("1 código no es un oficio de la obra") });
  await app.iniciar();
  app.obra = "9999";
  await app.cargar();

  await app.decidir(["9001", "9002"], "mismo");

  assert.equal(app.errorDecision, "1 código no es un oficio de la obra");
  assert.deepEqual(
    llamadas.map((l) => l.nombre),
    ["identidad", "propuestasCatalogos", "decidirCatalogos"],
  );
  assert.equal(app.decidiendo, false);
});

test("f036 R52: si las propuestas fallan, se dice y no queda nada pintado", async () => {
  const { app } = componente({ propuestasCatalogos: errorApi("sin Sigrid") });
  app.obra = "9999";
  app.vista = { obra: "vieja" };

  await app.cargar();

  assert.equal(app.errorCarga, "sin Sigrid");
  assert.equal(app.vista, null);
  assert.equal(app.cargando, false);
});

test("f036: sin obra no se piden propuestas", async () => {
  const { app, llamadas } = componente();
  app.obra = "  ";

  await app.cargar();

  assert.equal(llamadas.length, 0);
});

test("f036 R98: el boton de grupos vigentes guarda el JSON de la obra cargada", async () => {
  const { app, guardados } = componente();
  app.obra = "9999";
  await app.cargar();

  app.descargarGrupos();

  assert.equal(guardados.length, 1);
  assert.equal(guardados[0].nombre, "grupos_vigentes_oficio_9999.json");
  assert.deepEqual(JSON.parse(await guardados[0].blob.text()), { obra: "9999", oficio: [["9001", "9002"]] });
});

test("f036 R98: sin propuestas cargadas no hay grupos que descargar", () => {
  const { app, guardados } = componente();

  app.descargarGrupos();

  assert.equal(guardados.length, 0);
});

test("f036: el componente no expone nada que edite, descarte o apruebe incidencias (F-038)", () => {
  const { app } = componente();
  const nombres = Object.keys(app).join(" ").toLowerCase();

  for (const prohibido of ["editar", "descartar", "aprobar", "rechazar", "cerrar", "archivar", "importar"]) {
    assert.ok(!nombres.includes(prohibido), `el componente tiene algo de «${prohibido}»`);
  }
});
