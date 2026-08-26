// services/postventa-front/tests_js/traza.test.js
// R28 · Ni un dato personal en ningún registro del front.
//
// Todos los valores de este fichero están INVENTADOS. El DNI y las
// observaciones que aparecen aquí no son de nadie: son la carnaza con la que
// se comprueba que el filtro los tira.

const test = require("node:test");
const assert = require("node:assert/strict");

const { traza, sanear, CLAVES_PERMITIDAS } = require("../js/traza.js");

// Datos inventados que NUNCA deben salir por un registro.
const DNI_INVENTADO = "00000000T";
const OBSERVACIONES_INVENTADAS = "Inventado: el cliente no estaba en casa";

/** Recoge lo que se escribiría en consola, sin escribir en consola. */
function recolector() {
  const escrito = [];
  const salida = (evento) => escrito.push(evento);
  return { escrito, salida };
}

test("f007 R28: solo salen hash, paso, estado y http", () => {
  const { escrito, salida } = recolector();

  traza(
    { hash: "a1b2c3", paso: "validar", estado: "listo", http: 200 },
    salida,
  );

  assert.equal(escrito.length, 1);
  assert.deepEqual(escrito[0], {
    hash: "a1b2c3",
    paso: "validar",
    estado: "listo",
    http: 200,
  });
});

test("f007 R28: las claves permitidas son exactamente cuatro", () => {
  assert.deepEqual(CLAVES_PERMITIDAS, ["hash", "paso", "estado", "http"]);
});

test("f007 R28: un DNI o unas observaciones que se cuelen se descartan", () => {
  const { escrito, salida } = recolector();

  // Alguien pasa el parte entero por descuido. El filtro tiene que aguantarlo.
  traza(
    {
      hash: "a1b2c3",
      paso: "extraer",
      estado: "error",
      http: 502,
      dni_cliente: DNI_INVENTADO,
      observaciones: OBSERVACIONES_INVENTADAS,
      nombre_cliente: "Inventado Inventado",
      descripcion: "texto libre del parte",
    },
    salida,
  );

  const serializado = JSON.stringify(escrito);
  assert.ok(!serializado.includes(DNI_INVENTADO), "el DNI ha salido en la traza");
  assert.ok(
    !serializado.includes(OBSERVACIONES_INVENTADAS),
    "las observaciones han salido en la traza",
  );
  assert.deepEqual(Object.keys(escrito[0]).sort(), [
    "estado",
    "hash",
    "http",
    "paso",
  ]);
});

test("f007 R28: un objeto anidado bajo una clave permitida tampoco pasa", () => {
  // El filtro por claves no vería un dato personal escondido dentro de un
  // objeto: por eso solo se admiten primitivos.
  const limpio = sanear({
    hash: "a1b2c3",
    estado: { campo: "dni_cliente", valor: DNI_INVENTADO },
    paso: ["extraer", OBSERVACIONES_INVENTADAS],
    http: 200,
  });

  assert.deepEqual(limpio, { hash: "a1b2c3", http: 200 });
  assert.ok(!JSON.stringify(limpio).includes(DNI_INVENTADO));
});

test("f007 R28: las claves ausentes no se inventan", () => {
  assert.deepEqual(sanear({ hash: "a1b2c3" }), { hash: "a1b2c3" });
  assert.deepEqual(sanear({ hash: "a1b2c3", http: undefined }), {
    hash: "a1b2c3",
  });
  assert.deepEqual(sanear({ hash: "a1b2c3", http: null }), { hash: "a1b2c3" });
});

test("f007 R28: un evento que no es un objeto no revienta ni escribe basura", () => {
  assert.deepEqual(sanear(null), {});
  assert.deepEqual(sanear(undefined), {});
  assert.deepEqual(sanear("un texto suelto"), {});
  assert.deepEqual(sanear(42), {});
});

test("f007 R28: traza devuelve lo saneado, para que se pueda afirmar", () => {
  const { salida } = recolector();
  const devuelto = traza({ hash: "a1b2c3", http: 409, sobra: DNI_INVENTADO }, salida);

  assert.deepEqual(devuelto, { hash: "a1b2c3", http: 409 });
});

test("f007 R28: el objeto original no se modifica", () => {
  const evento = { hash: "a1b2c3", dni_cliente: DNI_INVENTADO };
  const { salida } = recolector();

  traza(evento, salida);

  assert.equal(evento.dni_cliente, DNI_INVENTADO, "sanear no muta la entrada");
});

test("f007 R28: sin salida inyectada escribe por consola, y solo lo saneado", () => {
  // Se sustituye console.info a propósito: es la única forma de comprobar el
  // camino por defecto sin ensuciar la salida de la suite.
  const original = console.info;
  const escrito = [];
  console.info = (evento) => escrito.push(evento);
  try {
    traza({ hash: "a1b2c3", paso: "firma", observaciones: OBSERVACIONES_INVENTADAS });
  } finally {
    console.info = original;
  }

  assert.deepEqual(escrito, [{ hash: "a1b2c3", paso: "firma" }]);
});
