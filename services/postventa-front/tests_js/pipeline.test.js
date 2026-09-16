// services/postventa-front/tests_js/pipeline.test.js
// R8, R13-R22, R29 · La orquestación de UN parte.
//
// TODOS los valores de este fichero están INVENTADOS: `0677`,
// `RS26.08/0123`, `00000000T`. Los partes de verdad llevan DNI y
// observaciones manuscritas de clientes y no entran en el repositorio (R30).

const test = require("node:test");
const assert = require("node:assert/strict");

const {
  CAMPOS_DEL_PARTE,
  UMBRAL_CONFIANZA,
  procesarParte,
  revalidar,
  cuerpoDeValidacion,
  aplicarEdiciones,
  cuerpoDeArchivo,
  esArchivable,
  semaforoDe,
  camposDudosos,
  ficheroDeParte,
} = require("../js/pipeline.js");

const HASH = "a1b2c3d4e5f6";

/** La respuesta que devolvería `/api/extraer`, con los NUEVE campos. */
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

/** La respuesta que devolvería `/api/firma`. */
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

function validacionInventada(veredicto, destino, motivos) {
  return {
    hash_parte: HASH,
    veredicto: veredicto,
    destino: destino,
    motivos: motivos || [],
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
      modo_deteccion: "pie_de_pagina",
      avisos: [],
      // F-019 R27 · desde que `POST /api/archivar` exige que el parte conste
      // guardado, «archivable» incluye «ya guardado». Se pone en el fixture
      // común porque es el estado normal de un parte procesado, y los tests de
      // F-007 que aquí importan son los del cuerpo de archivo, no los del
      // guardado. Lo que ese requisito fija tiene su propio fichero:
      // `tests_js/persistencia.test.js`.
      guardado: true,
      // Enmienda del 2026-09-16 · F-028 T17 · el bloque `estado` que devuelve
      // el backend. Se pone en el fixture común por el mismo motivo que
      // `guardado`: desde F-028, lo que abre el circuito es el estado del
      // parte y no su veredicto (R33), así que el estado normal de un parte
      // procesado y dado por bueno lo incluye. Lo que ese requisito fija tiene
      // su propio fichero: `tests_js/estado.test.js`.
      estadoParte: { estado: "aprobado", decidido_por_persona: false },
      fichero: new File([new Uint8Array([0x25, 0x50])], "parte-inventado.pdf"),
    },
    extra || {},
  );
}

function diferida() {
  let resolver;
  const promesa = new Promise((res) => {
    resolver = res;
  });
  return { promesa, resolver };
}

function respirar() {
  return new Promise((res) => setImmediate(res));
}

// --- R8 · extraer y firma en paralelo, validar después ---------------------

test("f007 R8: extraer y firma se piden EN PARALELO", async () => {
  const extraer = diferida();
  const firma = diferida();
  const llamadas = [];

  const api = {
    extraer: () => {
      llamadas.push("extraer");
      return extraer.promesa;
    },
    firma: () => {
      llamadas.push("firma");
      return firma.promesa;
    },
    validar: () => {
      llamadas.push("validar");
      return Promise.resolve(validacionInventada("apto", "archivo_y_cierre"));
    },
  };

  const pendiente = procesarParte(parteInventado(), api);
  await respirar();

  assert.deepEqual(llamadas, ["extraer", "firma"], "las dos salen sin esperarse");

  extraer.resolver(extraccionInventada());
  firma.resolver(firmaInventada());
  await pendiente;

  assert.deepEqual(llamadas, ["extraer", "firma", "validar"]);
});

test("f007 R8: validar NO se pide hasta que las dos han respondido", async () => {
  const extraer = diferida();
  const firma = diferida();
  const llamadas = [];

  const api = {
    extraer: () => extraer.promesa,
    firma: () => firma.promesa,
    validar: (cuerpo) => {
      llamadas.push(cuerpo);
      return Promise.resolve(validacionInventada("apto", "archivo_y_cierre"));
    },
  };

  const pendiente = procesarParte(parteInventado(), api);

  extraer.resolver(extraccionInventada());
  await respirar();
  assert.equal(llamadas.length, 0, "con solo una respuesta, todavía no se valida");

  firma.resolver(firmaInventada());
  await pendiente;
  assert.equal(llamadas.length, 1);
});

test("f007 R8: el cuerpo de validar son las DOS respuestas verbatim", async () => {
  const extraccion = extraccionInventada();
  const firma = firmaInventada();
  let cuerpoEnviado = null;

  const api = {
    extraer: async () => extraccion,
    firma: async () => firma,
    validar: async (cuerpo) => {
      cuerpoEnviado = cuerpo;
      return validacionInventada("apto", "archivo_y_cierre");
    },
  };

  await procesarParte(parteInventado(), api);

  assert.deepEqual(cuerpoEnviado.firma, firma, "la firma va tal cual llegó");
  assert.deepEqual(cuerpoEnviado.extraccion.traza, extraccion.traza, "la traza no se toca");
  assert.equal(cuerpoEnviado.extraccion.hash_parte, HASH);
});

test("f007 R8: un fallo de extraer se propaga y no se valida a medias", async () => {
  const llamadas = [];
  const api = {
    extraer: async () => {
      throw new Error("502 del modelo");
    },
    firma: async () => firmaInventada(),
    validar: async () => {
      llamadas.push("validar");
      return validacionInventada("apto", "archivo_y_cierre");
    },
  };

  await assert.rejects(() => procesarParte(parteInventado(), api), /502 del modelo/);
  assert.deepEqual(llamadas, [], "sin extracción no hay veredicto que pedir");
});

// --- R18 · las nueve claves, siempre ---------------------------------------

test("f007 R18: el cuerpo de validar lleva SIEMPRE las nueve claves", () => {
  const incompleta = extraccionInventada();
  delete incompleta.campos.observaciones;
  delete incompleta.campos.unidad;

  const cuerpo = cuerpoDeValidacion(incompleta, firmaInventada());

  assert.deepEqual(Object.keys(cuerpo.extraccion.campos).sort(), [...CAMPOS_DEL_PARTE].sort());
  assert.equal(cuerpo.extraccion.campos.observaciones.valor, null);
  assert.equal(cuerpo.extraccion.campos.unidad.valor, null);
});

test("f007 R18: un campo vacío viaja como valor null, no como cadena vacía", () => {
  const extraccion = extraccionInventada();
  const cuerpo = cuerpoDeValidacion(extraccion, firmaInventada(), {
    descripcion: "   ",
  });

  assert.equal(cuerpo.extraccion.campos.descripcion.valor, null);
});

test("f007 R18: las nueve claves son las del dominio, ni una más", () => {
  assert.deepEqual(CAMPOS_DEL_PARTE, [
    "promocion",
    "codigo_obra",
    "unidad",
    "numero_incidencia",
    "fecha_servicio",
    "descripcion",
    "dni_cliente",
    "observaciones",
    "numero_pagina",
  ]);
});

// --- R16 / D3 · un campo corregido a mano vale 100 --------------------------

test("f007 R16: un campo corregido a mano viaja con confianza 100 (D3)", () => {
  const cuerpo = cuerpoDeValidacion(extraccionInventada(), firmaInventada(), {
    codigo_obra: "0678",
  });

  assert.equal(cuerpo.extraccion.campos.codigo_obra.valor, "0678");
  assert.equal(cuerpo.extraccion.campos.codigo_obra.confianza_pct, 100);
});

test("f007 R16: el campo corregido queda MARCADO como editado (D3)", () => {
  const editada = aplicarEdiciones(extraccionInventada(), { dni_cliente: "11111111H" });

  assert.equal(editada.campos.dni_cliente.editado, true);
  assert.equal(editada.campos.dni_cliente.confianza_pct, 100);
  assert.notEqual(
    editada.campos.codigo_obra.editado,
    true,
    "un campo que nadie tocó no se marca",
  );
});

test("f007 R16: corregir un campo no toca el resto del cuerpo ni la traza", () => {
  const original = extraccionInventada();
  const cuerpo = cuerpoDeValidacion(original, firmaInventada(), { unidad: "B-3" });

  assert.deepEqual(cuerpo.extraccion.traza, original.traza);
  assert.equal(cuerpo.extraccion.campos.promocion.confianza_pct, 97);
  assert.equal(cuerpo.extraccion.campos.promocion.valor, "PROMOCIÓN INVENTADA");
  assert.equal(original.campos.unidad.valor, "A-12", "la extracción original no se muta");
});

test("f007 R15: se destacan los campos por debajo del umbral del dominio", () => {
  assert.equal(UMBRAL_CONFIANZA, 50);
  assert.deepEqual(camposDudosos(extraccionInventada()), ["dni_cliente"]);
});

test("f007 R15: un campo corregido a mano deja de ser dudoso", () => {
  const editada = aplicarEdiciones(extraccionInventada(), { dni_cliente: "11111111H" });

  assert.deepEqual(camposDudosos(editada), [], "el semáforo tiene que poder ponerse verde");
});

// --- R17 · revalidar es UNA petición ---------------------------------------

test("f007 R17: revalidar llama SOLO a validar", async () => {
  const llamadas = [];
  const api = {
    extraer: async () => {
      llamadas.push("extraer");
      return extraccionInventada();
    },
    firma: async () => {
      llamadas.push("firma");
      return firmaInventada();
    },
    validar: async () => {
      llamadas.push("validar");
      return validacionInventada("apto", "archivo_y_cierre");
    },
  };

  const parte = parteInventado({
    extraccion: extraccionInventada(),
    firma: firmaInventada(),
    ediciones: { codigo_obra: "0678" },
  });

  const nueva = await revalidar(parte, api);

  assert.deepEqual(llamadas, ["validar"], "revalidar no gasta IA");
  assert.equal(nueva.veredicto, "apto");
});

test("f007 R17: revalidar sin extracción previa es un error de programación", async () => {
  const api = { validar: async () => validacionInventada("apto", "archivo_y_cierre") };

  await assert.rejects(() => revalidar(parteInventado(), api), /todavía no tiene/i);
});

// --- R13 · el semáforo ------------------------------------------------------
//
// Enmienda del 2026-09-16 · F-028 T17
//
// Aquí había tres casos que llamaban a `semaforoDe(validacion)` con un solo
// argumento y esperaban que el color saliera del veredicto y del destino:
//
//   · «f007 R13: el semáforo sale de veredicto y destino, no de una escala
//      nueva» — apto → verde, cola → ámbar, revisión → rojo;
//   · «f007 R13: sin veredicto todavía, no hay semáforo que pintar»;
//   · «f007 R13: un apto con destino que no es archivo_y_cierre NO es verde».
//
// Se retiran porque **derivar el color del veredicto es exactamente lo que
// F-028 prohíbe** (R17): mientras el semáforo saliera de ahí, un parte apto
// que una persona había rechazado se pintaba verde, que es el defecto que abre
// la feature. El estado lo manda ahora el backend y la pantalla solo lo pinta.
//
// No se han «adaptado» pasándoles un segundo argumento, que es lo que los
// habría dejado verdes probando otra cosa. Sus sustitutos están en
// `tests_js/estado.test.js`, y cubren más de lo que cubrían estos:
//
//   · las cuatro marcas, estado a estado, incluidas `rechazado` y `cerrado`,
//     que antes no existían;
//   · el ámbar y el rojo, que son lo único que sigue saliendo del destino, y
//     ahora solo **dentro** de `pendiente`;
//   · «sin el bloque del backend NO se inventa ninguna marca», que es el
//     heredero directo del «sin veredicto no hay semáforo» y va al mismo lado
//     seguro: sin marca, nunca con la de aprobado;
//   · y R39, la distinción entre el aprobado de la máquina y el de una
//     persona, que aquí no se podía ni escribir.
//
// Lo que sí sigue en este fichero es `esArchivable`, y a propósito: conserva
// su significado de siempre —«lo que la máquina dio por bueno»— porque lo usa
// `noArchivables()` y porque distinguirlo del aprobado a mano es el requisito.

// --- R21 · nunca se archiva lo que no es apto ------------------------------

test("f007 R21: solo es archivable apto + archivo_y_cierre", () => {
  assert.equal(esArchivable(validacionInventada("apto", "archivo_y_cierre")), true);
  assert.equal(esArchivable(validacionInventada("apto", "revision_manual")), false);
  assert.equal(esArchivable(validacionInventada("no_apto", "archivo_y_cierre")), false);
  assert.equal(
    esArchivable(validacionInventada("no_apto", "cola_validacion_humana")),
    false,
  );
  assert.equal(esArchivable(null), false);
  assert.equal(esArchivable({}), false);
});

test("f007 R21 / f028 R33: componer el cuerpo de archivo de un parte no aprobado es imposible", () => {
  // No basta con no pintar el botón: aunque se pulse dos veces, aquí se para.
  //
  // Enmienda del 2026-09-16 · F-028 T17: lo que se niega ya no es «no es
  // apto» sino «no consta aprobado». El caso del parte apto rechazado a mano
  // —el que la feature viene a arreglar— está en `tests_js/estado.test.js`.
  const parte = parteInventado({
    extraccion: extraccionInventada(),
    validacion: validacionInventada("no_apto", "cola_validacion_humana"),
    estadoParte: { estado: "pendiente", decidido_por_persona: false },
  });

  assert.throws(() => cuerpoDeArchivo(parte), /no consta aprobado/i);
});

test("f007 R21: un parte ya archivado no se vuelve a componer", () => {
  const parte = parteInventado({
    extraccion: extraccionInventada(),
    validacion: validacionInventada("apto", "archivo_y_cierre"),
    archivado: true,
  });

  assert.throws(() => cuerpoDeArchivo(parte), /ya (está|esta) archivado/i);
});

// --- R20 / R29 · el cuerpo de archivar, exactamente cinco campos -----------

test("f007 R20: el cuerpo de archivar lleva el fichero y los cinco campos", () => {
  const parte = parteInventado({
    extraccion: extraccionInventada(),
    validacion: validacionInventada("apto", "archivo_y_cierre"),
  });

  const cuerpo = cuerpoDeArchivo(parte);

  assert.deepEqual([...cuerpo.keys()].sort(), [
    "codigo_obra",
    "destino",
    "fichero",
    "hash",
    "numero_incidencia",
    "veredicto",
  ]);
  assert.equal(cuerpo.get("hash"), HASH);
  assert.equal(cuerpo.get("codigo_obra"), "0677");
  assert.equal(cuerpo.get("numero_incidencia"), "RS26.08/0123");
  assert.equal(cuerpo.get("veredicto"), "apto");
  assert.equal(cuerpo.get("destino"), "archivo_y_cierre");
});

test("f007 R29: al archivar NO viajan ni el DNI ni las observaciones", () => {
  const DNI_INVENTADO = "00000000T";
  const OBSERVACIONES_INVENTADAS = "Inventado: el cliente no estaba";
  const extraccion = extraccionInventada();
  extraccion.campos.observaciones = {
    valor: OBSERVACIONES_INVENTADAS,
    confianza_pct: 90,
  };

  const cuerpo = cuerpoDeArchivo(
    parteInventado({
      extraccion: extraccion,
      validacion: validacionInventada("apto", "archivo_y_cierre"),
    }),
  );

  const claves = [...cuerpo.keys()];
  assert.ok(!claves.includes("dni_cliente"), "el DNI no puede viajar al archivar");
  assert.ok(!claves.includes("observaciones"));
  assert.ok(!claves.includes("descripcion"));

  const valores = claves
    .map((k) => cuerpo.get(k))
    .filter((v) => typeof v === "string")
    .join(" ");
  assert.ok(!valores.includes(DNI_INVENTADO));
  assert.ok(!valores.includes(OBSERVACIONES_INVENTADAS));
});

test("f007 R20: el cuerpo de archivo usa el valor CORREGIDO del código de obra", () => {
  const parte = parteInventado({
    extraccion: extraccionInventada(),
    validacion: validacionInventada("apto", "archivo_y_cierre"),
    ediciones: { codigo_obra: "0678" },
  });

  assert.equal(cuerpoDeArchivo(parte).get("codigo_obra"), "0678");
});

// --- R14 · el PDF del parte, desde el base64 de /api/split -----------------

test("f007 R14: el PDF del parte se reconstruye desde contenido_b64", () => {
  // Cuatro bytes inventados: "%PDF" en base64, no un parte real.
  const parte = { hash: HASH, contenido_b64: "JVBERg==" };

  const fichero = ficheroDeParte(parte);

  assert.equal(fichero.type, "application/pdf");
  assert.equal(fichero.size, 4, "los cuatro bytes de %PDF, ni uno inventado");
  assert.match(fichero.name, new RegExp(HASH.slice(0, 8)));
});

test("f007 R14: sin contenido_b64 no se inventa un PDF vacío", () => {
  assert.throws(() => ficheroDeParte({ hash: HASH }), /contenido/i);
});
