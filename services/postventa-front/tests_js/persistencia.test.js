// services/postventa-front/tests_js/persistencia.test.js
// F-019 R25-R28 · El front llama a los endpoints de persistencia EN ORDEN.
//
// Sin este cableado, los tres endpoints de F-019 existirían y **nadie los
// llamaría**: exactamente el estado que la feature viene a arreglar, un nivel
// más arriba. Y el archivado real seguiría sin poder completar en el circuito
// del piloto, porque `POST /api/archivar` responde 409 si el parte no consta
// guardado.
//
// Lo que se prueba aquí es **orden y consecuencias**, no formato:
//
//   R25 · la remesa se registra ANTES de procesar ningún parte;
//   R26 · guardar ocurre DESPUÉS de validar y ANTES de cualquier archivado;
//   R27 · un guardado fallido deja el parte NO archivable, con su motivo;
//   R28 · revalidar vuelve a guardar, para que lo guardado sea lo revisado.
//
// El doble de `api` registra el orden global de las llamadas: R25 y R26 no son
// afirmaciones sobre qué recibió cada endpoint, son afirmaciones sobre la
// secuencia, y eso no se puede comprobar endpoint a endpoint.
//
// TODOS los valores están INVENTADOS: `0677`, `RS26.08/0123`, `00000000T`.
// Los partes de verdad llevan DNI y observaciones manuscritas de clientes y no
// entran en el repositorio.

const test = require("node:test");
const assert = require("node:assert/strict");

const {
  procesarParte,
  revalidarYGuardar,
  guardarParte,
  cuerpoDeParte,
  cuerpoDeArchivo,
} = require("../js/pipeline.js");

const HASH = "a1b2c3d4e5f6";

//: Un UUID inventado para el test. El front solo lo transporta.
const REMESA_ID = "remesa-inventada-de-test";

function extraccionInventada(sobrescribir) {
  const campos = {
    promocion: { valor: "PROMOCIÓN INVENTADA", confianza_pct: 97 },
    codigo_obra: { valor: "0677", confianza_pct: 95 },
    unidad: { valor: "A-12", confianza_pct: 91 },
    numero_incidencia: { valor: "RS26.08/0123", confianza_pct: 88 },
    fecha_servicio: { valor: "2026-08-03", confianza_pct: 93 },
    descripcion: { valor: "Inventado: revisar el grifo", confianza_pct: 80 },
    dni_cliente: { valor: "00000000T", confianza_pct: 42 },
    observaciones: { valor: "", confianza_pct: 99 },
    numero_pagina: { valor: "1", confianza_pct: 99 },
  };
  return Object.assign(
    {
      hash_parte: HASH,
      campos: campos,
      traza: {
        proveedor: "inventado",
        modelo: "modelo-inventado",
        prompt_key: "extraccion",
        version_prompt: "1",
        huella_prompt: "0000",
      },
      avisos: [],
    },
    sobrescribir || {},
  );
}

function firmaInventada() {
  return {
    hash_parte: HASH,
    firma: { clasificacion: "firmado_conforme", confianza_pct: 96 },
    traza: {
      proveedor: "inventado",
      modelo: "modelo-inventado",
      prompt_key: "firma",
      version_prompt: "1",
      huella_prompt: "0000",
    },
    avisos: [],
  };
}

function validacionInventada(veredicto, destino) {
  return {
    hash_parte: HASH,
    veredicto: veredicto || "apto",
    destino: destino || "archivo_y_cierre",
    motivos: [],
    firma: { clasificacion: "firmado_conforme", confianza_pct: 96 },
    observaciones: "",
    avisos: [],
  };
}

function parteInventado(extra) {
  return Object.assign(
    {
      hash: HASH,
      origen: "remesa-inventada.pdf",
      paginas_origen: [1],
      modo_deteccion: "una_pagina_por_parte",
      avisos: [],
      ediciones: {},
      guardado: false,
      fichero: new File([new Uint8Array([0x25, 0x50])], "parte-inventado.pdf"),
    },
    extra || {},
  );
}

/**
 * Un `api` de mentira que apunta el ORDEN de todo lo que le piden.
 *
 * `fallos` permite que una operación concreta reviente sin tocar las demás:
 * es como se prueba R27 sin red.
 */
function apiFalsa(opciones) {
  const ajustes = opciones || {};
  const llamadas = [];
  const cuerpos = [];

  function registrar(nombre, cuerpo, respuesta) {
    llamadas.push(nombre);
    cuerpos.push({ nombre: nombre, cuerpo: cuerpo });
    const fallo = (ajustes.fallos || {})[nombre];
    if (fallo) {
      return Promise.reject(fallo);
    }
    return Promise.resolve(respuesta);
  }

  const api = {
    registrarRemesa: (cuerpo) =>
      registrar("registrarRemesa", cuerpo, {
        remesa_id: REMESA_ID,
        resultado: "creado",
      }),
    extraer: () => registrar("extraer", null, extraccionInventada()),
    firma: () => registrar("firma", null, firmaInventada()),
    validar: (cuerpo) =>
      registrar(
        "validar",
        cuerpo,
        ajustes.validacion || validacionInventada(),
      ),
    guardarParte: (cuerpo) =>
      registrar("guardarParte", cuerpo, {
        hash_parte: HASH,
        resultado_parte: "creado",
        resultado_validacion: "creado",
        avisos: [],
      }),
    archivar: (cuerpo) => registrar("archivar", cuerpo, { estado: "archivado" }),
    cola: () => registrar("cola", null, { total: 0, entradas: [] }),
  };

  return { api, llamadas, cuerpos };
}

/** El cuerpo con el que se llamó a esa operación. */
function cuerpoDe(cuerpos, nombre) {
  const hallado = cuerpos.find((c) => c.nombre === nombre);
  assert.ok(hallado, `no se llamó a ${nombre}`);
  return hallado.cuerpo;
}

// --- R26 · guardar va después de validar y antes de archivar ---------------

test("f019 R26: guardar el parte ocurre DESPUÉS de validar", async () => {
  const { api, llamadas } = apiFalsa();

  await procesarParte(parteInventado(), api, REMESA_ID);

  assert.deepEqual(llamadas, ["extraer", "firma", "validar", "guardarParte"]);
});

test("f019 R26: el cuerpo de guardar lleva remesa_id y el bloque parte", async () => {
  const { api, cuerpos } = apiFalsa();

  await procesarParte(parteInventado(), api, REMESA_ID);
  const cuerpo = cuerpoDe(cuerpos, "guardarParte");

  assert.equal(cuerpo.remesa_id, REMESA_ID);
  assert.equal(cuerpo.parte.hash, HASH);
  assert.equal(cuerpo.parte.origen, "remesa-inventada.pdf");
  assert.deepEqual(cuerpo.parte.paginas_origen, [1]);
  assert.equal(cuerpo.parte.modo_deteccion, "una_pagina_por_parte");
});

test("f019 R26: el cuerpo de guardar NO lleva los bytes del PDF", async () => {
  const { api, cuerpos } = apiFalsa();

  await procesarParte(parteInventado(), api, REMESA_ID);
  const cuerpo = cuerpoDe(cuerpos, "guardarParte");
  const serializado = JSON.stringify(cuerpo);

  assert.equal(cuerpo.parte.contenido_b64, undefined);
  assert.equal(cuerpo.parte.fichero, undefined);
  assert.ok(!serializado.includes("JVBER"), "no viaja base64 de PDF");
});

test("f019 R26: guardar lleva los MISMOS bloques que se validaron", async () => {
  const { api, cuerpos } = apiFalsa();

  await procesarParte(parteInventado(), api, REMESA_ID);
  const validado = cuerpoDe(cuerpos, "validar");
  const guardado = cuerpoDe(cuerpos, "guardarParte");

  assert.deepEqual(guardado.extraccion, validado.extraccion);
  assert.deepEqual(guardado.firma, validado.firma);
});

test("f019 R26: un parte guardado bien queda archivable", async () => {
  const { api } = apiFalsa();
  const parte = parteInventado();

  const resultado = await procesarParte(parte, api, REMESA_ID);

  assert.equal(resultado.guardado.ok, true);
  assert.equal(resultado.guardado.motivo, "");
});

// --- R27 · un guardado fallido deja el parte NO archivable -----------------

test("f019 R27: si guardar falla, el parte NO queda archivable y dice por qué", async () => {
  const { api } = apiFalsa({
    fallos: {
      guardarParte: { tipo: "no_apto", mensaje: "la remesa no consta" },
    },
  });

  const resultado = await procesarParte(parteInventado(), api, REMESA_ID);

  assert.equal(resultado.guardado.ok, false);
  assert.match(resultado.guardado.motivo, /no consta/);
});

test("f019 R27: un guardado fallido NO tira el veredicto ya obtenido", async () => {
  const { api } = apiFalsa({
    fallos: { guardarParte: { tipo: "entorno", mensaje: "la base no responde" } },
  });

  const resultado = await procesarParte(parteInventado(), api, REMESA_ID);

  assert.equal(resultado.validacion.veredicto, "apto");
  assert.ok(resultado.extraccion, "la extracción se conserva");
  assert.equal(resultado.guardado.ok, false);
});

test("f019 R27: cuerpoDeArchivo se NIEGA a componer un parte sin guardar", () => {
  const parte = parteInventado({
    validacion: validacionInventada(),
    guardado: false,
  });

  assert.throws(() => cuerpoDeArchivo(parte), /no.*guardad/i);
});

test("f019 R27: y sí lo compone en cuanto el parte consta guardado", () => {
  const parte = parteInventado({
    validacion: validacionInventada(),
    guardado: true,
  });

  const cuerpo = cuerpoDeArchivo(parte);

  assert.equal(cuerpo.get("hash"), HASH);
});

test("f019 R27: sin remesa registrada, el parte tampoco es archivable", async () => {
  const { api, llamadas } = apiFalsa();

  const resultado = await procesarParte(parteInventado(), api, "");

  assert.equal(resultado.guardado.ok, false);
  assert.match(resultado.guardado.motivo, /remesa/i);
  assert.ok(
    !llamadas.includes("guardarParte"),
    "sin remesa_id no se manda una petición que el backend va a rechazar",
  );
});

// --- R28 · revalidar vuelve a guardar --------------------------------------

test("f019 R28: revalidar vuelve a guardar, en ese orden", async () => {
  const { api, llamadas } = apiFalsa();
  const parte = parteInventado({
    extraccion: extraccionInventada(),
    firma: firmaInventada(),
    validacion: validacionInventada(),
    guardado: true,
    ediciones: { codigo_obra: "0678" },
  });

  await revalidarYGuardar(parte, api, REMESA_ID);

  assert.deepEqual(llamadas, ["validar", "guardarParte"]);
});

test("f019 R28: lo que se vuelve a guardar es lo REVISADO, no lo que dijo la IA", async () => {
  const { api, cuerpos } = apiFalsa();
  const parte = parteInventado({
    extraccion: extraccionInventada(),
    firma: firmaInventada(),
    validacion: validacionInventada(),
    guardado: true,
    ediciones: { codigo_obra: "0678" },
  });

  await revalidarYGuardar(parte, api, REMESA_ID);
  const guardado = cuerpoDe(cuerpos, "guardarParte");

  assert.equal(guardado.extraccion.campos.codigo_obra.valor, "0678");
  assert.equal(guardado.extraccion.campos.codigo_obra.confianza_pct, 100);
  assert.equal(guardado.extraccion.campos.codigo_obra.editado, true);
});

test("f019 R28: revalidar devuelve el veredicto nuevo Y el resultado de guardar", async () => {
  const { api } = apiFalsa();
  const parte = parteInventado({
    extraccion: extraccionInventada(),
    firma: firmaInventada(),
    validacion: validacionInventada(),
    guardado: true,
  });

  const resultado = await revalidarYGuardar(parte, api, REMESA_ID);

  assert.equal(resultado.validacion.veredicto, "apto");
  assert.equal(resultado.guardado.ok, true);
});

test("f019 R28: si al revalidar falla el guardado, el parte deja de ser archivable", async () => {
  const { api } = apiFalsa({
    fallos: { guardarParte: { tipo: "entorno", mensaje: "la base no responde" } },
  });
  const parte = parteInventado({
    extraccion: extraccionInventada(),
    firma: firmaInventada(),
    validacion: validacionInventada(),
    guardado: true,
    ediciones: { codigo_obra: "0678" },
  });

  const resultado = await revalidarYGuardar(parte, api, REMESA_ID);

  assert.equal(resultado.guardado.ok, false);
});

// --- El cuerpo de /api/parte, aislado --------------------------------------

test("f019 R26: cuerpoDeParte compone las cuatro claves del contrato", () => {
  const parte = parteInventado({
    extraccion: extraccionInventada(),
    firma: firmaInventada(),
  });

  const cuerpo = cuerpoDeParte(parte, REMESA_ID);

  assert.deepEqual(Object.keys(cuerpo).sort(), [
    "extraccion",
    "firma",
    "parte",
    "remesa_id",
  ]);
});

test("f019 R26: cuerpoDeParte lleva SIEMPRE los nueve campos", () => {
  const incompleta = extraccionInventada();
  delete incompleta.campos.observaciones;
  delete incompleta.campos.unidad;

  const cuerpo = cuerpoDeParte(
    parteInventado({ extraccion: incompleta, firma: firmaInventada() }),
    REMESA_ID,
  );

  assert.equal(Object.keys(cuerpo.extraccion.campos).length, 9);
  assert.equal(cuerpo.extraccion.campos.unidad.valor, null);
});

// --- guardarParte, aislado -------------------------------------------------

test("f019 R27: guardarParte nunca lanza; devuelve el motivo", async () => {
  const { api } = apiFalsa({
    fallos: { guardarParte: { mensaje: "409 la remesa no consta" } },
  });
  const parte = parteInventado({
    extraccion: extraccionInventada(),
    firma: firmaInventada(),
  });

  const guardado = await guardarParte(parte, api, REMESA_ID);

  assert.equal(guardado.ok, false);
  assert.match(guardado.motivo, /409/);
});

test("f019 R27: un error sin mensaje tampoco se traga en silencio", async () => {
  const { api } = apiFalsa({ fallos: { guardarParte: new Error("boom") } });
  const parte = parteInventado({
    extraccion: extraccionInventada(),
    firma: firmaInventada(),
  });

  const guardado = await guardarParte(parte, api, REMESA_ID);

  assert.equal(guardado.ok, false);
  assert.ok(guardado.motivo.length > 0, "siempre hay un motivo que enseñar");
});
