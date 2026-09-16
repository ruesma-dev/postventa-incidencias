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

// Enmienda del 2026-09-16 · F-028 T17: de los trece nombres que importaba este
// fichero quedan tres. Los diez que se van -`esCirculable`, `semaforoDe`,
// `cuerpoDeArchivo`, `cuerpoDeCierre`, `cuerpoDeGrafico`, `esArchivable`,
// `esCerrable`, `guardarParte`, `pendientesDeCircuito` y `cuerpoDeParte`- se
// quedaban sin un solo llamante aquí, y un import sin uso es una pista falsa
// sobre lo que un fichero prueba. `cuerpoDeParte` se queda: lo sigue usando el
// caso que compara el cuerpo de aprobar con el de guardar.
const {
  MOTIVOS_APROBABLES,
  esAprobable,
  cuerpoDeAprobacion,
  cuerpoDeParte,
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
// Enmienda del 2026-09-16 · F-028 T17 · el semáforo y el circuito se mudan
// ===========================================================================
//
// Aquí vivían once casos sobre `semaforoDe(validacion, aprobacion)` y
// `esCirculable(parte)` tal y como los dejó F-026. Se retiran porque prueban
// **el mecanismo que T17 sustituye**, no un comportamiento que siga
// existiendo: el color y la entrada al circuito salían del veredicto y de una
// aprobación con su destino, y desde F-028 salen del bloque `estado` que manda
// el backend (R17, R33). La caducidad ya no se recomputa en pantalla: la
// resuelve el backend al derivar (R19).
//
// Ninguno se ha «adaptado» pasándole un bloque `estado`, que es lo que los
// habría dejado verdes probando otra cosa con nombre de F-026. Sus sustitutos
// están escritos y en verde en `tests_js/estado.test.js`:
//
//   RETIRADO (semáforo)                              SUSTITUTO EN F-028
//   · R36 «aprobado y vigente se pinta 'aprobado',   · R39 «un parte aprobado POR UNA PERSONA no se
//     nunca 'verde'»                                   pinta igual que el verde»
//   · R36 «el aprobado se distingue del verde        · R39 «y la marca depende de QUIÉN decidió, no
//     también viniendo de revisión manual»             del veredicto»
//   · R31 «una aprobación revocada devuelve el       · R17 «sin el bloque del backend NO se inventa
//     parte a su color de origen»                      ninguna marca» + R38 «un parte pendiente sigue
//                                                      siendo ámbar o rojo, según su destino»
//   · R36 «la aprobación no cambia el color de un    · R38 «un parte aprobado POR LA MÁQUINA se pinta
//     parte que ya era verde»                          verde»
//   · f007 R13 «sin aprobación, el semáforo sigue    · R38 (ámbar y rojo) + R17 (sin bloque, sin
//     diciendo exactamente lo que decía»               marca). Este dejó de ser cierto a propósito:
//                                                      F-028 SÍ reescribe los tres colores de F-007, y
//                                                      esa es justamente la feature.
//
//   RETIRADO (circuito)                              SUSTITUTO EN F-028
//   · R23 «el apto de siempre entra, sin que nadie   · R33 «entra en la tanda el que está APROBADO, lo
//     apruebe nada»                                    diga la máquina o una persona»
//   · R23 «un no apto con aprobación viva del mismo  · R9 «un parte NO APTO que una persona aprobó
//     destino entra en el circuito»                    entra en la tanda»
//   · R25 «un no apto sin aprobación NO entra»       · R4 «un parte PENDIENTE sale de la tanda»
//   · R31 «con la aprobación revocada se queda       · R17 «sin bloque de estado el parte NO entra en
//     fuera»                                           la tanda»
//   · «una aprobación de otro destino no vale»       · ídem — F-028 no compara destinos: el backend
//                                                      compara la huella del veredicto entero, que es
//                                                      más estrecho y no más laxo
//   · «sin veredicto no circula nada»                · R17 «sin bloque de estado el parte NO entra»
//
// Y uno que aquí no se podía ni escribir, que es el encargo de la feature:
// `estado.test.js` · R5 «un parte RECHAZADO sale de la tanda AUNQUE su
// veredicto sea apto».
//
// Lo que NO se ha tocado de este fichero: `MOTIVOS_APROBABLES`, `esAprobable`
// y `cuerpoDeAprobacion`, que siguen vivos porque `js/app.js` e `index.html`
// los siguen llamando. Se van con T18, que es quien reescribe la pantalla.

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

// ===========================================================================
// Enmienda del 2026-09-16 · F-028 T17 · la tanda, las tres composiciones y lo
// que llega del backend al guardar
// ===========================================================================
//
// Aquí vivían catorce casos más: `parteAprobado`, la entrada en la tanda de
// F-025, las tres composiciones (`cuerpoDeArchivo`, `esCerrable`,
// `cuerpoDeGrafico`) y el bloque `aprobacion` que `guardarParte` sacaba de la
// respuesta. Se retiran por lo mismo que los de arriba —prueban el mecanismo
// que T17 sustituye— y con una razón añadida en los cuatro últimos: desde T14
// el backend **ya no emite** ningún bloque `aprobacion`, así que
// `guardado.aprobacion` era una clave que no podía llegar nunca.
//
// Cuatro de los catorce **seguían en verde** después del cambio, y por eso
// merecen su párrafo: «un no apto sin aprobación sigue fuera de la tanda», «un
// aprobado que no consta guardado tampoco entra», «el cuerpo de archivo se
// sigue negando sin aprobación ninguna» y «un revocado ni se cierra ni se
// adjunta» pasaban porque el montaje se había quedado **inerte** —le pasan una
// `aprobacion` a un pipeline al que ya nadie se la pide, así que el parte se
// queda fuera por no tener estado, no por lo que el nombre del test afirma—. Es
// la clase de test verde que tranquiliza sin medir nada, y el mismo motivo por
// el que el bloque 4 retiró cinco casos de `test_f026_puertas.py` y T15 otros
// dos.
//
//   RETIRADO                                         SUSTITUTO EN F-028
//   · R23 «un aprobado vigente entra en la tanda»    · R33 «entra en la tanda el que está APROBADO…»
//   · R25 «un no apto sin aprobación sigue fuera»    · R4 «un parte PENDIENTE sale de la tanda»
//   · R31 «un aprobado revocado se queda fuera»      · R17 «sin bloque de estado el parte NO entra»
//   · f019 R27 «un aprobado sin guardar tampoco      · R34 «el estado no relaja las otras puertas de
//     entra»                                           la tanda»
//   · R23 «el cuerpo de archivo se compone para un   · R33 y R9; y que lo que se declara es el
//     parte aprobado»                                  veredicto REAL lo fija `estado.test.js` con
//                                                      «no viaja NI UN BYTE del PDF ni un veredicto ya
//                                                      hecho»
//   · R31 «el cuerpo de archivo se niega para un     · R5 «el cuerpo de archivo se NIEGA a componer un
//     revocado»                                        parte apto rechazado»
//   · R25 «el cuerpo de archivo se sigue negando     · ídem, y R7 «un parte cerrado tampoco compone
//     sin aprobación ninguna»                          ninguna de las tres»
//   · R23 «un aprobado archivado es cerrable, y      · R33 (`esCirculable` de los dos aprobados) y los
//     adjuntable»                                      fixtures de `cierre.test.js` y `grafico.test.js`,
//                                                      que ya montan el estado
//   · R31 «un revocado ni se cierra ni se adjunta»   · R5 «un parte apto rechazado NO es cerrable ni
//                                                      adjuntable, aunque conste archivado»
//   · R36 «`esArchivable` conserva su significado»   · **se conserva donde vive**: `pipeline.test.js` ·
//                                                      «f007 R21: solo es archivable apto +
//                                                      archivo_y_cierre»
//   · R22 «al guardar, la aprobación llega al        · R38 «al guardar, el estado que devuelve el
//     parte»                                           backend llega al parte»
//   · R31 «si el backend dice que la revocó, eso     · **Sin sustituto, y a propósito**: F-028 no
//     es lo que llega»                                 revoca nada. La aprobación caduca al derivar, y
//                                                      eso se prueba en el backend
//                                                      (`test_f028_r19_…`, `test_f028_r20_…`)
//   · R22 «sin aprobación en la respuesta, lo que    · «sin bloque de estado en la respuesta, lo que
//     llega es null y no un hueco»                     llega es null y no un hueco»
//   · «un guardado fallido no inventa ninguna        · «un guardado fallido no inventa ningún estado»
//     aprobación»
//
// Con ellos se va `FormDataFalso`, que se quedaba sin un solo llamante.
