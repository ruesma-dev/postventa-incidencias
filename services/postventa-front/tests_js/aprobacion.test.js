// services/postventa-front/tests_js/aprobacion.test.js
// F-026 · Lo que la pantalla decide sobre una aprobación humana.
//
// Aquí se prueba la mitad de la feature que vive en el front y que SÍ decide
// algo: si este parte se puede ofrecer para aprobar, si un parte aprobado
// entra en el circuito, qué viaja en la petición de aprobación y —lo que esta
// feature existe para registrar— que un parte aprobado **no se pinta igual**
// que uno que siempre fue verde (R36).
//
// La decisión de verdad la toma el backend: `es_aprobable` y `admite_circuito`
// viven en `domain/models/aprobacion.py` y se vuelven a evaluar en cada
// petición. Lo de aquí solo evita ofrecer un botón que va a responder 409, y
// negarse a componer un cuerpo que el backend rechazaría.
//
// TODOS los valores están INVENTADOS: el código de obra, el de incidencia y el
// `oid`. Los partes de verdad llevan DNI y observaciones manuscritas de
// clientes y no entran en el repositorio.

const test = require("node:test");
const assert = require("node:assert/strict");

const {
  MOTIVOS_APROBABLES,
  esAprobable,
  esCirculable,
  cuerpoDeAprobacion,
  cuerpoDeParte,
  cuerpoDeArchivo,
  cuerpoDeCierre,
  cuerpoDeGrafico,
  esArchivable,
  esCerrable,
  guardarParte,
  pendientesDeCircuito,
  semaforoDe,
} = require("../js/pipeline.js");

const HASH = "a1b2c3d4e5f6";
const OID = "oid-inventado-para-el-test";
const REMESA = "remesa-inventada-de-test";

/** Un motivo tal y como lo emite F-004: código y texto para Posventa. */
function motivo(codigo) {
  return { codigo: codigo, texto: `texto inventado de ${codigo}` };
}

/** El veredicto que devuelve `/api/validar`. */
function validacionInventada(veredicto, destino, motivos) {
  return {
    hash_parte: HASH,
    veredicto: veredicto,
    destino: destino,
    motivos: motivos || [],
    firma: { clasificacion: "ilegible", confianza_pct: 40 },
    observaciones: "",
    avisos: [],
  };
}

/** El veredicto ámbar típico: hay observaciones manuscritas que juzgar. */
function validacionDeLaCola() {
  return validacionInventada("no_apto", "cola_validacion_humana", [
    motivo("observaciones_manuscritas"),
  ]);
}

/** El bloque `aprobacion` tal y como lo emite el backend (R22). */
function aprobacionInventada(sobrescribir) {
  return Object.assign(
    {
      estado: "aprobado",
      destino_aprobado: "cola_validacion_humana",
      motivos_aprobados: ["observaciones_manuscritas"],
      aprobado_at_utc: "2026-09-12T10:12:00+00:00",
    },
    sobrescribir || {},
  );
}

/** La extracción de `/api/extraer`, con los NUEVE campos. */
function extraccionInventada() {
  return {
    hash_parte: HASH,
    campos: {
      promocion: { valor: "PROMOCIÓN INVENTADA", confianza_pct: 97 },
      codigo_obra: { valor: "0677", confianza_pct: 95 },
      unidad: { valor: "A-12", confianza_pct: 91 },
      numero_incidencia: { valor: "RS26.08/0123", confianza_pct: 88 },
      fecha_servicio: { valor: "2026-08-03", confianza_pct: 93 },
      descripcion: { valor: "Inventado: revisar el grifo", confianza_pct: 80 },
      dni_cliente: { valor: "00000000T", confianza_pct: 42 },
      observaciones: { valor: "Inventado: no se reparó del todo", confianza_pct: 77 },
      numero_pagina: { valor: "1", confianza_pct: 99 },
    },
    traza: { proveedor: "inventado", modelo: "modelo-inventado" },
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
      guardado: true,
      archivado: false,
      cerrado: false,
      ediciones: {},
      extraccion: extraccionInventada(),
      firma: { hash_parte: HASH, firma: { clasificacion: "ilegible" } },
      validacion: validacionDeLaCola(),
      aprobacion: null,
      contenido_b64: "JVBERi0xLjQK",
      fichero: new File([new Uint8Array([0x25, 0x50])], "parte-inventado.pdf"),
    },
    extra || {},
  );
}

// ===========================================================================
// R6-R9 · qué se puede ofrecer para aprobar
// ===========================================================================

test("f026 R6: la lista de motivos aprobables es la del dominio, y solo esos dos", () => {
  // Ampliarla ensancha la única puerta por la que un parte rechazado llega al
  // ERP de producción: si esta lista cambia sin que cambie
  // `domain/models/aprobacion.py::MOTIVOS_APROBABLES`, el front ofrece un
  // botón que el backend contesta con un 409.
  assert.deepEqual(MOTIVOS_APROBABLES.slice().sort(), [
    "firma_no_humana",
    "observaciones_manuscritas",
  ]);
});

test("f026 R8: un parte con observaciones manuscritas es aprobable", () => {
  assert.equal(esAprobable(validacionDeLaCola()), true);
});

test("f026 R8: un parte con la firma no humana es aprobable", () => {
  const validacion = validacionInventada("no_apto", "revision_manual", [
    motivo("firma_no_humana"),
  ]);

  assert.equal(esAprobable(validacion), true);
});

test("f026 R9: con un motivo fuera de la lista NO es aprobable, aunque haya otro que sí", () => {
  // El parte que trae observaciones y además ha perdido el código de obra no
  // se aprueba: archivarlo lo metería en una carpeta inventada. No es
  // política, es que ahí no hay nada que decidir, hay algo que teclear.
  const validacion = validacionInventada("no_apto", "revision_manual", [
    motivo("observaciones_manuscritas"),
    motivo("codigo_obra_no_legible"),
  ]);

  assert.equal(esAprobable(validacion), false);
});

test("f026 R9: sin código de obra o sin número de incidencia no es aprobable", () => {
  for (const codigo of ["codigo_obra_no_legible", "numero_incidencia_no_legible"]) {
    const validacion = validacionInventada("no_apto", "revision_manual", [
      motivo(codigo),
    ]);

    assert.equal(esAprobable(validacion), false, `${codigo} no puede ser aprobable`);
  }
});

test("f026 R10: un parte que la máquina dio por bueno no tiene nada que aprobar", () => {
  assert.equal(esAprobable(validacionInventada("apto", "archivo_y_cierre")), false);
});

test("f026: sin veredicto no se ofrece aprobar nada", () => {
  // «No hay veredicto» se arregla revalidando el parte, no aprobándolo.
  assert.equal(esAprobable(null), false);
  assert.equal(esAprobable(undefined), false);
  assert.equal(esAprobable({}), false);
  assert.equal(
    esAprobable(validacionInventada("no_apto", "cola_validacion_humana")),
    false,
    "un no apto sin motivos no es aprobable: no se sabe qué se estaría aprobando",
  );
});

// ===========================================================================
// R36 · el cuarto estado del semáforo: un parte aprobado NO es un verde más
// ===========================================================================

test("f026 R36: un parte aprobado y vigente se pinta 'aprobado', nunca 'verde'", () => {
  const semaforo = semaforoDe(validacionDeLaCola(), aprobacionInventada());

  assert.equal(semaforo, "aprobado");
  assert.notEqual(
    semaforo,
    "verde",
    "uno lo dio por bueno la máquina y el otro una persona A PESAR de la " +
      "máquina: pintarlos igual borra el dato que F-026 existe para registrar",
  );
});

test("f026 R36: el aprobado se distingue del verde también viniendo de revisión manual", () => {
  const validacion = validacionInventada("no_apto", "revision_manual", [
    motivo("firma_no_humana"),
  ]);
  const aprobacion = aprobacionInventada({ destino_aprobado: "revision_manual" });

  assert.equal(semaforoDe(validacion, aprobacion), "aprobado");
});

test("f026 R31: una aprobación revocada devuelve el parte a su color de origen", () => {
  // La corrección de un campo cambió el veredicto, así que nadie ha opinado
  // sobre lo nuevo: vuelve a hacer falta que una persona lo mire.
  const revocada = aprobacionInventada({ estado: "revocado" });

  assert.equal(semaforoDe(validacionDeLaCola(), revocada), "ambar");
});

test("f026 R36: la aprobación no cambia el color de un parte que ya era verde", () => {
  const apto = validacionInventada("apto", "archivo_y_cierre");

  assert.equal(semaforoDe(apto, aprobacionInventada()), "verde");
});

test("f007 R13: sin aprobación, el semáforo sigue diciendo exactamente lo que decía", () => {
  // Control negativo: F-026 añade un estado, no reescribe los tres de F-007.
  assert.equal(semaforoDe(validacionInventada("apto", "archivo_y_cierre")), "verde");
  assert.equal(semaforoDe(validacionDeLaCola()), "ambar");
  assert.equal(
    semaforoDe(validacionInventada("no_apto", "revision_manual")),
    "rojo",
  );
  assert.equal(semaforoDe(null), "");
  assert.equal(semaforoDe(null, aprobacionInventada()), "");
});

// ===========================================================================
// R23, R25, R31 · qué entra en el circuito
// ===========================================================================

test("f026 R23: el apto de siempre entra en el circuito, sin que nadie apruebe nada", () => {
  const parte = parteInventado({
    validacion: validacionInventada("apto", "archivo_y_cierre"),
  });

  assert.equal(esCirculable(parte), true);
});

test("f026 R23: un no apto con aprobación viva del mismo destino entra en el circuito", () => {
  const parte = parteInventado({ aprobacion: aprobacionInventada() });

  assert.equal(esCirculable(parte), true);
});

test("f026 R25: un no apto sin aprobación NO entra en el circuito", () => {
  assert.equal(esCirculable(parteInventado()), false);
});

test("f026 R31: con la aprobación revocada, el parte vuelve a quedarse fuera", () => {
  const parte = parteInventado({
    aprobacion: aprobacionInventada({ estado: "revocado" }),
  });

  assert.equal(esCirculable(parte), false);
});

test("f026: una aprobación de otro destino no vale para el veredicto de ahora", () => {
  // Si el parte pasó de la cola ámbar a revisión manual, la aprobación de la
  // cola no dice nada de lo nuevo. Es lo mismo que comprueba
  // `admite_circuito` en el backend, que es quien decide de verdad.
  const parte = parteInventado({
    validacion: validacionInventada("no_apto", "revision_manual", [
      motivo("firma_no_humana"),
    ]),
    aprobacion: aprobacionInventada({ destino_aprobado: "cola_validacion_humana" }),
  });

  assert.equal(esCirculable(parte), false);
});

test("f026: sin veredicto no circula nada, ni con aprobación delante", () => {
  const parte = parteInventado({
    validacion: null,
    aprobacion: aprobacionInventada(),
  });

  assert.equal(esCirculable(parte), false);
  assert.equal(esCirculable(null), false);
  assert.equal(esCirculable(undefined), false);
});

// ===========================================================================
// R4, R19 · qué viaja en la petición de aprobación
// ===========================================================================

test("f026 R4: sin saber quién aprueba no se compone ninguna petición", () => {
  // Sin identificador no se puede registrar la decisión, y registrar quién
  // decidió es la mitad de esta feature.
  assert.throws(
    () => cuerpoDeAprobacion(parteInventado(), { remesaId: REMESA }),
    /identificador/,
  );
  assert.throws(
    () => cuerpoDeAprobacion(parteInventado(), { remesaId: REMESA, usuarioOid: "" }),
    /identificador/,
  );
});

test("f026 R29: la petición declara la confirmación con el booleano de JSON", () => {
  const cuerpo = cuerpoDeAprobacion(parteInventado(), {
    remesaId: REMESA,
    usuarioOid: OID,
  });

  assert.equal(cuerpo.usuario_oid, OID);
  assert.equal(cuerpo.confirmado, true, "el backend solo acepta el true de JSON");
});

test("f026 R19: el cuerpo de aprobar es el de guardar MÁS dos claves, y ni una más", () => {
  // El backend recalcula el veredicto con `validar_parte` (R5) y necesita
  // exactamente lo mismo que `/api/parte`: los nueve campos y la lectura de
  // firma. Recortar la extracción cambiaría el veredicto que se aprueba —sin
  // las observaciones el parte ni siquiera sería aprobable—, así que lo que
  // se fija aquí es que F-026 **no añade** nada personal por su cuenta.
  const parte = parteInventado();
  const deGuardar = cuerpoDeParte(parte, REMESA);
  const deAprobar = cuerpoDeAprobacion(parte, {
    remesaId: REMESA,
    usuarioOid: OID,
  });

  const nuevas = Object.keys(deAprobar).filter(
    (clave) => Object.keys(deGuardar).indexOf(clave) === -1,
  );
  assert.deepEqual(nuevas.sort(), ["confirmado", "usuario_oid"]);
  assert.deepEqual(deAprobar.extraccion, deGuardar.extraccion);
  assert.deepEqual(deAprobar.parte, deGuardar.parte);
});

test("f026 R19: no viajan ni los bytes del PDF ni un veredicto ya hecho", () => {
  // El documento vive en SharePoint y el veredicto lo emite el backend: si
  // llegara hecho, quien llama se declararía aprobable y aprobaría un parte al
  // que le falta el código de obra.
  const cuerpo = cuerpoDeAprobacion(parteInventado(), {
    remesaId: REMESA,
    usuarioOid: OID,
  });
  const texto = JSON.stringify(cuerpo);

  assert.equal("veredicto" in cuerpo, false);
  assert.equal("validacion" in cuerpo, false);
  assert.equal("contenido_b64" in cuerpo, false);
  assert.equal(texto.indexOf("JVBERi0xLjQK"), -1, "los bytes del PDF no viajan");
  assert.equal(texto.indexOf("no_apto"), -1, "el veredicto no viaja hecho");
});

test("f026 R9: componer la aprobación de un parte NO aprobable se niega, no lo apaña", () => {
  // No basta con no pintar el botón: aunque se pulse dos veces, aquí se para.
  const parte = parteInventado({
    validacion: validacionInventada("no_apto", "revision_manual", [
      motivo("codigo_obra_no_legible"),
    ]),
  });

  assert.throws(
    () => cuerpoDeAprobacion(parte, { remesaId: REMESA, usuarioOid: OID }),
    /no se puede aprobar/,
  );
});

test("f026: sin remesa registrada no se compone nada, porque el backend responde 409", () => {
  assert.throws(
    () => cuerpoDeAprobacion(parteInventado(), { usuarioOid: OID }),
    /remesa/,
  );
});

// ===========================================================================
// R23, R25 · el circuito entero pasa por `esCirculable`
// ===========================================================================
//
// No basta con que `esCirculable` diga la verdad: lo que decide si un parte
// aprobado llega a SharePoint y al ERP son los cuatro sitios que lo usan. Si
// uno solo se quedara mirando `esArchivable`, la feature entera se quedaría en
// una marca de color, y encima el botón parecería funcionar.

/** Un `FormData` de mentira que recuerda lo que le metieron. */
class FormDataFalso {
  constructor() {
    this.campos = [];
  }
  append(nombre, valor, nombreFichero) {
    this.campos.push({ nombre, valor, nombreFichero });
  }
  get(nombre) {
    const encontrado = this.campos.find((campo) => campo.nombre === nombre);
    return encontrado ? encontrado.valor : null;
  }
}

/** El parte aprobado, guardado y listo para entrar en la tanda. */
function parteAprobado(extra) {
  return parteInventado(
    Object.assign({ aprobacion: aprobacionInventada() }, extra || {}),
  );
}

test("f026 R23: un aprobado vigente entra en la tanda de la confirmación única", () => {
  const tanda = pendientesDeCircuito([parteAprobado()]);

  assert.equal(tanda.length, 1);
});

test("f026 R25: un no apto sin aprobación sigue fuera de la tanda", () => {
  // Es el control negativo de F-025 R36, y tiene que seguir en pie: lo que
  // F-026 abre es la puerta de los aprobados, no la de los rechazados.
  assert.deepEqual(pendientesDeCircuito([parteInventado()]), []);
});

test("f026 R31: un aprobado revocado vuelve a quedarse fuera de la tanda", () => {
  const revocado = parteAprobado({
    aprobacion: aprobacionInventada({ estado: "revocado" }),
  });

  assert.deepEqual(pendientesDeCircuito([revocado]), []);
});

test("f019 R27: un aprobado que no consta guardado tampoco entra en la tanda", () => {
  // La aprobación no relaja ninguna otra puerta (R26): sin fila en la base,
  // `/api/archivar` responde 409 y no sube nada.
  assert.deepEqual(pendientesDeCircuito([parteAprobado({ guardado: false })]), []);
});

test("f026 R23: el cuerpo de archivo se compone para un parte aprobado", () => {
  const cuerpo = cuerpoDeArchivo(parteAprobado(), FormDataFalso);

  assert.equal(cuerpo.get("hash"), HASH);
  assert.equal(cuerpo.get("codigo_obra"), "0677");
  assert.equal(
    cuerpo.get("veredicto"),
    "no_apto",
    "lo que se declara es el veredicto REAL: la aprobación va al lado, nunca encima",
  );
  assert.equal(cuerpo.get("destino"), "cola_validacion_humana");
});

test("f026 R31: el cuerpo de archivo se niega a componer para un revocado", () => {
  const revocado = parteAprobado({
    aprobacion: aprobacionInventada({ estado: "revocado" }),
  });

  assert.throws(() => cuerpoDeArchivo(revocado, FormDataFalso), /no es apto/i);
});

test("f026 R25: el cuerpo de archivo se sigue negando sin aprobación ninguna", () => {
  assert.throws(() => cuerpoDeArchivo(parteInventado(), FormDataFalso), /no es apto/i);
});

test("f026 R23: un aprobado archivado es cerrable, y adjuntable", () => {
  const parte = parteAprobado({ archivado: true });

  assert.equal(esCerrable(parte), true);
  assert.doesNotThrow(() =>
    cuerpoDeGrafico(parte, { usuarioOid: OID }, FormDataFalso),
  );
});

test("f026 R31: un revocado ni se cierra ni se adjunta, aunque conste archivado", () => {
  const revocado = parteAprobado({
    archivado: true,
    aprobacion: aprobacionInventada({ estado: "revocado" }),
  });

  assert.equal(esCerrable(revocado), false);
  assert.throws(
    () => cuerpoDeGrafico(revocado, { usuarioOid: OID }, FormDataFalso),
    /no se puede adjuntar/,
  );
  assert.throws(() => cuerpoDeCierre(revocado, { usuarioOid: OID }), /no se puede cerrar/);
});

test("f026 R36: `esArchivable` conserva su significado: lo que dio por bueno LA MÁQUINA", () => {
  // Es la distinción que la feature existe para registrar, y `noArchivables()`
  // depende de ella: si `esArchivable` empezara a decir «o lo aprobó alguien»,
  // no quedaría ninguna forma de contar las dos cosas por separado.
  const parte = parteAprobado();

  assert.equal(esArchivable(parte.validacion), false);
  assert.equal(esCirculable(parte), true);
});

// ===========================================================================
// R22, R31 · la aprobación llega del backend en cada guardado
// ===========================================================================
//
// Sin esto la pantalla solo sabría de aprobaciones las que se hayan hecho en
// esta pestaña: al volver a subir la remesa —que es como se recupera el
// trabajo tras recargar— los partes aprobados volverían a parecer rechazados.
// Y, peor, una aprobación **revocada** por la revalidación seguiría pintada
// como viva hasta que alguien recargase.

/** Un `api` de mentira que devuelve lo que se le diga al guardar. */
function apiQueGuarda(respuesta) {
  return {
    guardarParte: async () => respuesta,
    validar: async () => validacionDeLaCola(),
  };
}

test("f026 R22: al guardar, la aprobación que devuelve el backend llega al parte", async () => {
  const api = apiQueGuarda({ hash_parte: HASH, aprobacion: aprobacionInventada() });

  const guardado = await guardarParte(parteInventado(), api, REMESA);

  assert.equal(guardado.ok, true);
  assert.equal(guardado.aprobacion.estado, "aprobado");
  assert.equal(guardado.aprobacion.destino_aprobado, "cola_validacion_humana");
});

test("f026 R31: si el backend dice que la revocó, eso es lo que llega", async () => {
  // La revocación ocurre en la escritura (D-F): guardar una validación cuyo
  // veredicto cambió revoca la aprobación en la misma operación. La pantalla
  // se entera por la respuesta de ese mismo guardado, no en la recarga
  // siguiente.
  const api = apiQueGuarda({
    hash_parte: HASH,
    aprobacion: aprobacionInventada({ estado: "revocado" }),
  });

  const guardado = await guardarParte(parteInventado(), api, REMESA);

  assert.equal(guardado.aprobacion.estado, "revocado");
});

test("f026 R22: sin aprobación en la respuesta, lo que llega es null y no un hueco", async () => {
  const api = apiQueGuarda({ hash_parte: HASH, aprobacion: null });

  const guardado = await guardarParte(parteInventado(), api, REMESA);

  assert.equal(guardado.aprobacion, null);
});

test("f026: un guardado fallido no inventa ninguna aprobación", async () => {
  const api = {
    guardarParte: async () => {
      throw new Error("inventado: el backend no responde");
    },
  };

  const guardado = await guardarParte(parteInventado(), api, REMESA);

  assert.equal(guardado.ok, false);
  assert.equal(guardado.aprobacion, null);
});
