// services/postventa-front/tests_js/seleccion.test.js
// R1-R4 · La selección de ficheros y el multipart de la remesa.
//
// Todos los nombres de fichero son INVENTADOS. No hay ni un parte real en el
// repositorio (R30): aquí se fabrican `File` de dos bytes con contenido
// inventado.

const test = require("node:test");
const assert = require("node:assert/strict");

const {
  filtrarAdmitidos,
  motivoDeRechazo,
  formDataDeRemesa,
  formatearTamano,
  extensionDe,
  esAdmitido,
  PREFIJO_CAMPO,
} = require("../js/seleccion.js");

/** Un `File` de mentira, con lo único que mira el módulo: `name` y `size`. */
function ficheroFalso(nombre, tamano) {
  return { name: nombre, size: tamano === undefined ? 1024 : tamano };
}

/** Un `File` de verdad (Node 20+), para el `FormData` real. */
function ficheroReal(nombre) {
  return new File([new Uint8Array([0x25, 0x50])], nombre, {
    type: "application/pdf",
  });
}

test("f007 R1: una selección de PDFs y ZIPs se acepta entera", () => {
  const resultado = filtrarAdmitidos([
    ficheroFalso("remesa-inventada.pdf"),
    ficheroFalso("partes-inventados.zip"),
  ]);

  assert.equal(resultado.admitidos.length, 2);
  assert.deepEqual(resultado.descartados, []);
  assert.equal(resultado.mensajeDescartes, "");
  assert.equal(motivoDeRechazo(resultado), "");
});

test("f007 R1: cada fichero se puede listar con su nombre y su tamaño", () => {
  assert.equal(formatearTamano(512), "512 B");
  assert.equal(formatearTamano(2048), "2.0 KB");
  assert.equal(formatearTamano(3 * 1024 * 1024), "3.0 MB");
  assert.equal(formatearTamano(0), "0 B");
  assert.equal(formatearTamano(undefined), "tamaño desconocido");
  assert.equal(formatearTamano(-1), "tamaño desconocido");
});

test("f007 R2: de una carpeta solo se queda lo que el backend sabe trocear", () => {
  // Lo que trae de verdad una carpeta elegida con el selector del navegador.
  const resultado = filtrarAdmitidos([
    ficheroFalso("remesa-inventada.pdf"),
    ficheroFalso("foto-de-la-obra.jpg"),
    ficheroFalso("control-inventado.xlsx"),
    ficheroFalso("Thumbs.db"),
    ficheroFalso("partes-inventados.zip"),
    ficheroFalso("LEEME"),
  ]);

  assert.deepEqual(
    resultado.admitidos.map((f) => f.name),
    ["remesa-inventada.pdf", "partes-inventados.zip"],
  );
  assert.equal(resultado.descartados.length, 4);
});

test("f007 R2: se dice cuántos ficheros se han descartado y por qué", () => {
  const resultado = filtrarAdmitidos([
    ficheroFalso("remesa-inventada.pdf"),
    ficheroFalso("foto-de-la-obra.jpg"),
    ficheroFalso("LEEME"),
  ]);

  assert.match(resultado.mensajeDescartes, /2 fichero/);
  assert.deepEqual(resultado.descartados, [
    { nombre: "foto-de-la-obra.jpg", motivo: "formato .jpg no admitido" },
    { nombre: "LEEME", motivo: "sin extensión reconocible" },
  ]);
});

test("f007 R2: la extensión se reconoce sin importar mayúsculas", () => {
  const resultado = filtrarAdmitidos([
    ficheroFalso("REMESA-INVENTADA.PDF"),
    ficheroFalso("Partes.Zip"),
  ]);

  assert.equal(resultado.admitidos.length, 2);
  assert.equal(extensionDe("REMESA.PDF"), ".pdf");
  assert.equal(esAdmitido(ficheroFalso("x.PdF")), true);
});

test("f007 R2: un nombre con puntos no engaña al filtro", () => {
  assert.equal(esAdmitido(ficheroFalso("parte.pdf.exe")), false);
  assert.equal(esAdmitido(ficheroFalso("parte.2026.08.pdf")), true);
});

test("f007 R3: una selección sin PDF ni ZIP se rechaza y explica qué se admite", () => {
  const resultado = filtrarAdmitidos([
    ficheroFalso("foto-de-la-obra.jpg"),
    ficheroFalso("control-inventado.xlsx"),
  ]);

  assert.deepEqual(resultado.admitidos, []);
  const motivo = motivoDeRechazo(resultado);
  assert.match(motivo, /no contiene ningún PDF ni ZIP/i);
  assert.match(motivo, /\.pdf/);
  assert.match(motivo, /\.zip/);
});

test("f007 R3: una selección vacía también se rechaza en el navegador", () => {
  const resultado = filtrarAdmitidos([]);

  assert.deepEqual(resultado.admitidos, []);
  assert.notEqual(motivoDeRechazo(resultado), "");
});

test("f007 R3: sin ficheros admitidos no se puede ni construir el cuerpo del POST", () => {
  // La red no se toca: el módulo se niega antes de que exista una petición.
  assert.throws(() => formDataDeRemesa([]), /ningún fichero admitido/);
});

test("f007 R4: cada fichero viaja con un nombre de campo distinto", () => {
  const cuerpo = formDataDeRemesa([
    ficheroReal("remesa-inventada.pdf"),
    ficheroReal("partes-inventados.zip"),
    ficheroReal("otra-remesa-inventada.pdf"),
  ]);

  const claves = [...cuerpo.keys()];
  assert.deepEqual(claves, ["fichero_0", "fichero_1", "fichero_2"]);
  assert.equal(new Set(claves).size, 3, "no puede haber dos claves iguales");
  assert.equal(PREFIJO_CAMPO, "fichero_");
});

test("f007 R4: dos ficheros que se llaman IGUAL no comparten nombre de campo", () => {
  // El caso que perdería partes en silencio: el backend lee
  // req.files.values(), un valor por clave.
  const cuerpo = formDataDeRemesa([
    ficheroReal("remesa-inventada.pdf"),
    ficheroReal("remesa-inventada.pdf"),
  ]);

  const claves = [...cuerpo.keys()];
  assert.deepEqual(claves, ["fichero_0", "fichero_1"]);
  assert.equal(cuerpo.getAll("fichero_0").length, 1);
  assert.equal(cuerpo.getAll("fichero_1").length, 1);
});

test("f007 R4: el nombre original del fichero llega al backend", () => {
  const cuerpo = formDataDeRemesa([ficheroReal("remesa-inventada.pdf")]);

  assert.equal(cuerpo.get("fichero_0").name, "remesa-inventada.pdf");
});

test("f007 R4: una remesa de 22 partes son 22 campos distintos", () => {
  const ficheros = Array.from({ length: 22 }, (_, i) =>
    ficheroReal(`parte-inventado-${i}.pdf`),
  );

  const claves = [...formDataDeRemesa(ficheros).keys()];

  assert.equal(claves.length, 22);
  assert.equal(new Set(claves).size, 22);
});

test("f007 R4: el FormData es inyectable, para no depender del entorno", () => {
  const anotados = [];
  class FormDataFalso {
    append(clave, valor, nombre) {
      anotados.push({ clave, nombre });
    }
  }

  formDataDeRemesa([ficheroFalso("a.pdf"), ficheroFalso("b.pdf")], FormDataFalso);

  assert.deepEqual(anotados, [
    { clave: "fichero_0", nombre: "a.pdf" },
    { clave: "fichero_1", nombre: "b.pdf" },
  ]);
});
