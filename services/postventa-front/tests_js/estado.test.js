// services/postventa-front/tests_js/estado.test.js
// F-028 · Lo que la pantalla decide sobre el ESTADO de un parte.
//
// Dos mitades, y las dos viven en `js/pipeline.js`:
//
//   1. **Qué viaja** cuando una persona aprueba o rechaza un parte
//      (`cuerpoDeCambioDeEstado`, T16). El backend es quien decide de verdad
//      —`POST /api/estado` lo vuelve a comprobar todo—, pero componer un
//      cuerpo que va a responder 400 es pedirle al usuario que espere para
//      nada, y en el caso del rechazo sin motivo sería además perder lo único
//      que quien vuelva a mirar el parte va a necesitar (R11).
//   2. **Qué se pinta y qué circula** a partir del estado que devuelve el
//      backend (`semaforoDe` y el selector de la tanda, T17).
//
// La regla que ordena las dos: **el estado lo manda el backend y el front lo
// pinta**. Aquí no se deriva ningún estado (R17): no se mira el veredicto para
// adivinar si un parte está aprobado, se mira el bloque `estado` que vino en la
// respuesta. La única lectura del veredicto que queda es elegir entre ámbar y
// rojo dentro de `pendiente`, que es un matiz de color y no una decisión.
//
// TODOS los valores están INVENTADOS: el código de obra, el de incidencia, el
// `oid` y el motivo. Los partes de verdad llevan DNI y observaciones
// manuscritas de clientes y no entran en el repositorio.

const test = require("node:test");
const assert = require("node:assert/strict");

const {
  ESTADOS_MANUALES,
  LIMITE_MOTIVO,
  cuerpoDeCambioDeEstado,
  cuerpoDeParte,
} = require("../js/pipeline.js");

const HASH = "a1b2c3d4e5f6";
const OID = "oid-inventado-para-el-test";
const REMESA = "remesa-inventada-de-test";
const MOTIVO = "Inventado: la firma no es del cliente, hay que repetir la visita";

/** Los bytes del PDF, en base64. NO deben viajar en esta petición (R30). */
const PDF_B64 = "JVBERi0xLjQKJUlOVkVOVEFETw==";

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

/** El parte tal y como lo tiene la pantalla: con su PDF y su veredicto. */
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
      validacion: validacionInventada("no_apto", "cola_validacion_humana", [
        { codigo: "observaciones_manuscritas", texto: "texto inventado" },
      ]),
      contenido_b64: PDF_B64,
      fichero: { name: "parte-inventado.pdf", bytes: PDF_B64 },
    },
    extra || {},
  );
}

/** Las opciones completas: el caso que sí compone. */
function opciones(extra) {
  return Object.assign(
    { estado: "rechazado", usuarioOid: OID, remesaId: REMESA, motivo: MOTIVO },
    extra || {},
  );
}

// ==========================================================================
// T16 · R10 · los destinos manuales son DOS, y no hay más
// ==========================================================================

test("f028 R10: los dos únicos destinos manuales son aprobado y rechazado", () => {
  // Copia de `ESTADOS_MANUALES` del handler: a `pendiente` no se vuelve a mano
  // y a `cerrado` solo se llega cerrando la incidencia en el ERP.
  assert.deepEqual(ESTADOS_MANUALES, ["aprobado", "rechazado"]);
});

test("f028 R10: no se compone ningún cambio a un estado que no sea manual", () => {
  for (const estado of ["pendiente", "cerrado", "aprobada", "", null, undefined]) {
    assert.throws(
      () => cuerpoDeCambioDeEstado(parteInventado(), opciones({ estado: estado })),
      /aprobado.*rechazado|rechazado.*aprobado/i,
      `«${estado}» no debería componerse`,
    );
  }
});

// ==========================================================================
// T16 · R11, R14 · las dos puertas: sin motivo no se rechaza, sin oid no se
//                  decide nada
// ==========================================================================

test("f028 R11: un rechazo SIN motivo no se compone, y se dice por qué", () => {
  // La puerta de verdad está en el backend, que responde 400. Esta es la
  // primera de las dos, y hace falta: mandar el rechazo y que lo rechace el
  // backend deja al usuario con un error genérico donde tenía que haber un
  // campo de texto pidiéndole que explique la decisión.
  for (const motivo of [undefined, null, "", "   ", "\n\t "]) {
    assert.throws(
      () =>
        cuerpoDeCambioDeEstado(
          parteInventado(),
          opciones({ estado: "rechazado", motivo: motivo }),
        ),
      /motivo/i,
      `un rechazo con motivo «${JSON.stringify(motivo)}» no debería componerse`,
    );
  }
});

test("f028 R12: al aprobar el motivo es opcional, y sin él el cuerpo no lo lleva", () => {
  // La asimetría es del dominio: al parte rechazado hay que volver, y quien
  // vuelva necesita saber qué había que arreglar. Aprobar no deja nada
  // pendiente.
  const cuerpo = cuerpoDeCambioDeEstado(
    parteInventado(),
    opciones({ estado: "aprobado", motivo: "" }),
  );

  assert.equal(cuerpo.estado, "aprobado");
  assert.ok(
    !Object.prototype.hasOwnProperty.call(cuerpo, "motivo"),
    "un motivo vacío no viaja como clave vacía: el backend distingue «no hay» de «está en blanco»",
  );
});

test("f028 R14: sin saber quién decide no se compone ninguna petición", () => {
  for (const oid of [undefined, null, "", "   "]) {
    assert.throws(
      () =>
        cuerpoDeCambioDeEstado(parteInventado(), opciones({ usuarioOid: oid })),
      /qui[eé]n/i,
      `un cambio de estado con oid «${JSON.stringify(oid)}» no debería componerse`,
    );
  }
});

test("f028 R11, R14: el rechazo sin motivo NI oid tampoco se cuela por el otro lado", () => {
  // Control negativo del control: que falle la primera puerta no puede dejar
  // pasar la segunda. Sin una de las dos, aquí no se compone nada.
  assert.throws(
    () =>
      cuerpoDeCambioDeEstado(
        parteInventado(),
        opciones({ usuarioOid: "", motivo: "" }),
      ),
    /qui[eé]n|motivo/i,
  );
});

test("f028: sin remesa registrada no se compone nada, porque el backend responde 409", () => {
  assert.throws(
    () => cuerpoDeCambioDeEstado(parteInventado(), opciones({ remesaId: "" })),
    /remesa/i,
  );
});

// ==========================================================================
// T16 · R13 · el motivo: recortado por los extremos y acotado
// ==========================================================================

test("f028 R13: el motivo viaja recortado por los extremos", () => {
  const cuerpo = cuerpoDeCambioDeEstado(
    parteInventado(),
    opciones({ motivo: `   ${MOTIVO}\n  ` }),
  );

  assert.equal(cuerpo.motivo, MOTIVO);
});

test("f028 R13: el límite del motivo es el del dominio, y pasarse se rechaza", () => {
  // `LIMITE_MOTIVO` es copia de `domain/models/estado.py`, igual que
  // `UMBRAL_CONFIANZA` y `CAMPOS_DEL_PARTE`. Y pasarse **se rechaza**, no se
  // recorta: recortar guardaría media frase y haría creer a quien la escribió
  // que se guardó entera.
  assert.equal(LIMITE_MOTIVO, 500);

  const justo = "x".repeat(LIMITE_MOTIVO);
  assert.equal(
    cuerpoDeCambioDeEstado(parteInventado(), opciones({ motivo: justo })).motivo,
    justo,
  );

  assert.throws(
    () =>
      cuerpoDeCambioDeEstado(
        parteInventado(),
        opciones({ motivo: "x".repeat(LIMITE_MOTIVO + 1) }),
      ),
    new RegExp(String(LIMITE_MOTIVO)),
  );
});

test("f028 R13: el motivo se acota DESPUÉS de recortar, no antes", () => {
  // Si se midiera el crudo, un motivo válido rodeado de espacios se
  // rechazaría por largo sin que quien lo escribió pudiera ver por qué.
  const justo = `  ${"x".repeat(LIMITE_MOTIVO)}  `;

  assert.equal(
    cuerpoDeCambioDeEstado(parteInventado(), opciones({ motivo: justo })).motivo
      .length,
    LIMITE_MOTIVO,
  );
});

// ==========================================================================
// T16 · R29, R30 · qué viaja exactamente, y qué no
// ==========================================================================

test("f028 R29: la confirmación viaja como el BOOLEANO de JSON, no como la cadena", () => {
  // El backend exige `crudo is not True` y rechaza a propósito la cadena
  // "true": es el error clásico de un front que serializa mal, y tratarlo como
  // confirmación dejaría un parte rechazado a nombre de alguien que no lo
  // rechazó. Se comprueba sobre el JSON ya serializado, que es lo que viaja.
  const cuerpo = cuerpoDeCambioDeEstado(parteInventado(), opciones());

  assert.equal(cuerpo.confirmado, true);
  assert.equal(typeof cuerpo.confirmado, "boolean");
  assert.ok(
    JSON.stringify(cuerpo).includes('"confirmado":true'),
    'lo que viaja tiene que ser `true`, nunca `"true"`',
  );
});

test("f028: el cuerpo es el de guardar MÁS las cuatro claves propias, y ni una más", () => {
  const parte = parteInventado();
  const cuerpo = cuerpoDeCambioDeEstado(parte, opciones());

  assert.deepEqual(Object.keys(cuerpo).sort(), [
    "confirmado",
    "estado",
    "extraccion",
    "firma",
    "motivo",
    "parte",
    "remesa_id",
    "usuario_oid",
  ]);

  // Y la mitad de guardar es LA MISMA que compone `cuerpoDeParte`: recortar la
  // extracción cambiaría el veredicto sobre el que se decide.
  const guardar = cuerpoDeParte(parte, REMESA);
  assert.deepEqual(cuerpo.remesa_id, guardar.remesa_id);
  assert.deepEqual(cuerpo.parte, guardar.parte);
  assert.deepEqual(cuerpo.extraccion, guardar.extraccion);
  assert.deepEqual(cuerpo.firma, guardar.firma);
  assert.equal(cuerpo.estado, "rechazado");
  assert.equal(cuerpo.usuario_oid, OID);
});

test("f028 R30: no viaja NI UN BYTE del PDF ni un veredicto ya hecho", () => {
  const parte = parteInventado();
  const serializado = JSON.stringify(
    cuerpoDeCambioDeEstado(parte, opciones()),
  );

  assert.ok(
    !serializado.includes(PDF_B64),
    "los bytes del PDF no viajan: el documento vive en SharePoint",
  );
  assert.ok(!serializado.includes("contenido_b64"));
  assert.ok(!serializado.includes("fichero"));
  assert.ok(
    !serializado.includes("veredicto"),
    "el veredicto se recalcula en el backend y no se acepta hecho (R28)",
  );
  assert.ok(!serializado.includes("destino"));
});

test("f028 R30: un veredicto metido a mano en el parte tampoco se cuela", () => {
  // Control negativo del control anterior: que el parte de prueba no lleve
  // `validacion` sería una comprobación que no sabe fallar.
  const parte = parteInventado();
  assert.equal(parte.validacion.veredicto, "no_apto");

  const cuerpo = cuerpoDeCambioDeEstado(parte, opciones());

  assert.ok(!Object.prototype.hasOwnProperty.call(cuerpo, "validacion"));
  assert.ok(!Object.prototype.hasOwnProperty.call(cuerpo, "veredicto"));
});

test("f028: las ediciones de la persona SÍ viajan, que es lo que se decide", () => {
  // El veredicto lo recalcula el backend sobre lo que se le manda. Si las
  // correcciones no viajaran, la decisión se tomaría sobre el parte sin
  // corregir y la huella apuntada no sería la del veredicto que se ve.
  const parte = parteInventado({ ediciones: { codigo_obra: "0999" } });

  const cuerpo = cuerpoDeCambioDeEstado(parte, opciones());

  assert.equal(cuerpo.extraccion.campos.codigo_obra.valor, "0999");
});
