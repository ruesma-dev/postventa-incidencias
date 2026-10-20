// services/postventa-front/tests_js/revision.test.js
// F-038 R3-R13, R22, R24 · La bandeja de revisión: lo puro y el componente.
//
// `specs/F-038-bandeja-revision/design.md` §2.4 y su tabla «Conciliado
// 2026-10-20», contra el contrato **implementado** del backend
// (`services/postventa-api/interface_adapters/api/revision.py` y
// `domain/models/revision.py`).
//
// Bloque 1 bis (T1 bis): al final, `bandeja.html` leída como texto y sus
// expresiones de Alpine evaluadas contra este componente (R10, R11, R13,
// R21.6).
//
// Bloque 1 ter (T4 bis): la presentación del volcado (R21: `lineaDeVolcado`,
// `textoMotivoVolcado`, los filtros `volcada` y `en_duda`, «Ya no se revisa
// aquí»), en lo puro, en el componente y en el recorrido de `bandeja.html`.
//
// Todo inventado: obra 9901, unidades U-01…, oficios 9001…, proveedores P-0N
// «Ejemplo», correos @ejemplo.invalid, UUID con ceros que no son de nadie.
// NI UN TEST ABRE RED: el componente recibe un `api` doble.

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const Revision = require("../js/revision.js");

const CORREO = "revisora@ejemplo.invalid";
const OTRO_CORREO = "otra.persona@ejemplo.invalid";
const OID = "oid-inventado-para-el-test";
const IDENTIDAD = { usuarioOid: OID, correo: CORREO };

const ID_1 = "00000000-0000-4000-8000-000000000001";
const ID_2 = "00000000-0000-4000-8000-000000000002";
const ID_3 = "00000000-0000-4000-8000-000000000003";
const ID_4 = "00000000-0000-4000-8000-000000000004";
const ID_FUERA = "00000000-0000-4000-8000-0000000000ff";

/** El `catalogo` de `GET /api/revision`, con la forma del handler. */
function catalogo() {
  return {
    unidades: [
      { codigo: "U-01", nombre: "Unidad Ejemplo Uno" },
      { codigo: "U-02", nombre: "Unidad Ejemplo Dos" },
      { codigo: "U-03", nombre: null },
    ],
    ubicaciones: {
      "U-01": ["Cocina ejemplo", "Baño ejemplo"],
      "U-02": ["Cocina ejemplo", "Terraza ejemplo"],
      "U-03": [],
    },
    oficios: [
      { codigo: "9003", nombre: "Pintura ejemplo", grupo: { etiqueta: "Pintura ejemplo", codigos: ["9003"] } },
      { codigo: "9001", nombre: "Fontaneria ejemplo A", grupo: { etiqueta: "Fontaneria ejemplo", codigos: ["9001", "9002"] } },
      { codigo: "9004", nombre: "Carpinteria ejemplo", grupo: { etiqueta: "Carpinteria ejemplo", codigos: ["9004"] } },
      { codigo: "9002", nombre: "Fontaneria ejemplo B", grupo: { etiqueta: "Fontaneria ejemplo", codigos: ["9001", "9002"] } },
    ],
    pares: [
      { oficio_codigo: "9001", proveedor_codigo: "P-01", proveedor_nombre: "Proveedor Ejemplo Uno" },
      { oficio_codigo: "9001", proveedor_codigo: "P-02", proveedor_nombre: null },
      { oficio_codigo: "9002", proveedor_codigo: "P-01", proveedor_nombre: "Proveedor Ejemplo Uno" },
      { oficio_codigo: "9003", proveedor_codigo: "P-03", proveedor_nombre: "Proveedor Ejemplo Tres" },
    ],
    urgencias: [
      { codigo: "normal", etiqueta: "Normal" },
      { codigo: "urgente", etiqueta: "Urgente" },
    ],
    listados: [
      { codigo: "repaso", etiqueta: "Repaso" },
      { codigo: "garantia", etiqueta: "Garantía" },
    ],
  };
}

/** Los trece valores de `importados` / `vigentes`. */
function valores(cambios) {
  return Object.assign(
    {
      unidad_codigo: "U-01",
      unidad_nombre: "Unidad Ejemplo Uno",
      ubicacion: "Cocina ejemplo",
      descripcion: "Grieta de ejemplo en el alicatado",
      detalle: null,
      oficio_codigo: "9001",
      oficio_nombre: "Fontaneria ejemplo A",
      oficio_ambiguo: false,
      proveedor_codigo: "P-01",
      proveedor_nombre: "Proveedor Ejemplo Uno",
      proveedor_ambiguo: false,
      urgencia: "normal",
      listado: "repaso",
    },
    cambios || {},
  );
}

/** Los valores de una fila con el oficio ambiguo (sin código, con su etiqueta). */
function valoresAmbiguos(cambios) {
  return valores(
    Object.assign(
      {
        oficio_codigo: null,
        oficio_nombre: "Fontaneria ejemplo",
        oficio_ambiguo: true,
        proveedor_codigo: null,
        proveedor_nombre: null,
      },
      cambios || {},
    ),
  );
}

/** Una incidencia de la respuesta, con la forma de `_fila` del handler. */
function incidencia(cambios) {
  const base = {
    incidencia_id: ID_1,
    origen: "excel",
    importacion_id: "00000000-0000-4000-8000-0000000000aa",
    fila_origen: 2,
    creada_at_utc: "2026-10-20T08:00:00.000000+00:00",
    duplicada_de: null,
    importados: valores(),
    vigentes: valores(),
    cambios: [],
    estado: "nueva",
    revision_id: null,
    revisado_at_utc: null,
    revisado_por: null,
    motivos_no_aprobable: [],
    volcado: null,
  };
  return Object.assign(base, cambios || {});
}

/** El `resumen` de la respuesta: seis estados, nueve motivos. */
function resumen(cambios) {
  return Object.assign(
    {
      total: 10,
      por_estado: { nueva: 4, editada: 2, aprobada: 1, descartada: 1, volcada: 1, en_duda: 1 },
      con_motivos: 3,
      por_motivo: {
        unidad_fuera_de_la_obra: 0,
        sin_ubicacion: 2,
        ubicacion_fuera_de_lista: 1,
        sin_oficio: 0,
        oficio_ambiguo: 1,
        oficio_fuera_de_la_obra: 0,
        par_fuera_de_la_obra: 0,
        proveedor_ambiguo: 0,
        duplicada: 0,
      },
    },
    cambios || {},
  );
}

/** Una respuesta entera de `GET /api/revision`. */
function respuesta(cambios) {
  return Object.assign(
    {
      obra: "9901",
      catalogo: catalogo(),
      resumen: resumen(),
      filtros: { estado: "activas", con_motivos: null },
      total_filtrado: 3,
      incidencias: [incidencia()],
      siguiente: null,
    },
    cambios || {},
  );
}

/** Un `ErrorApi` de mentira, con lo que deja `js/api.js` (R26). */
function errorApi(http, codigo, detalle, mensaje) {
  const texto = mensaje || "texto del servicio, inventado";
  const error = new Error(texto);
  error.tipo = http === null ? "transitorio" : "peticion";
  error.http = http;
  error.mensaje = texto;
  error.mensajeServicio = http === null ? null : texto;
  error.codigo = codigo || null;
  error.detalle = detalle === undefined ? null : detalle;
  return error;
}

// --- R4 (a) · los nueve motivos, en su orden -----------------------------------

test("f038 R4 (a): los nueve motivos de MotivoNoAprobable, en su orden y con su texto", () => {
  assert.deepEqual(Revision.MOTIVOS, [
    "unidad_fuera_de_la_obra",
    "sin_ubicacion",
    "ubicacion_fuera_de_lista",
    "sin_oficio",
    "oficio_ambiguo",
    "oficio_fuera_de_la_obra",
    "par_fuera_de_la_obra",
    "proveedor_ambiguo",
    "duplicada",
  ]);
  assert.equal(Revision.textoMotivo("unidad_fuera_de_la_obra"), "La unidad ya no es de la obra en Sigrid");
  assert.equal(Revision.textoMotivo("sin_ubicacion"), "Falta la ubicación");
  assert.equal(Revision.textoMotivo("ubicacion_fuera_de_lista"), "La ubicación no está en la lista");
  assert.equal(Revision.textoMotivo("sin_oficio"), "Falta el oficio");
  assert.equal(Revision.textoMotivo("oficio_ambiguo"), "Elige el código del oficio: hay varios en la obra");
  assert.equal(Revision.textoMotivo("oficio_fuera_de_la_obra"), "Este oficio ya no está en la obra en Sigrid");
  assert.equal(Revision.textoMotivo("par_fuera_de_la_obra"), "Este proveedor ya no está en la obra con ese oficio");
  assert.equal(Revision.textoMotivo("proveedor_ambiguo"), "Elige el proveedor");
  assert.match(Revision.textoMotivo("duplicada"), /^Duplicada/);
  for (const motivo of Revision.MOTIVOS) {
    assert.notEqual(Revision.textoMotivo(motivo), motivo, `${motivo} sin texto`);
  }
});

test("f038 R4 (a): un motivo desconocido se enseña tal cual, sin romper la fila", () => {
  assert.equal(Revision.textoMotivo("motivo_que_no_existe"), "motivo_que_no_existe");
  const fila = Revision.presentarRevision(
    respuesta({ incidencias: [incidencia({ motivos_no_aprobable: ["sin_ubicacion", "motivo_que_no_existe"] })] }),
  ).filas[0];
  assert.deepEqual(fila.motivos, ["Falta la ubicación", "motivo_que_no_existe"]);
});

// --- R4 (c), R21 · los seis estados ---------------------------------------------

test("f038 R4 (c): los seis estados con su etiqueta; uno desconocido, tal cual", () => {
  assert.deepEqual(Revision.ESTADOS, ["nueva", "editada", "aprobada", "descartada", "volcada", "en_duda"]);
  assert.equal(Revision.etiquetaEstado("nueva"), "Nueva");
  assert.equal(Revision.etiquetaEstado("editada"), "Editada");
  assert.equal(Revision.etiquetaEstado("aprobada"), "Aprobada");
  assert.equal(Revision.etiquetaEstado("descartada"), "Descartada");
  assert.equal(Revision.etiquetaEstado("volcada"), "Volcada a Sigrid");
  assert.equal(Revision.etiquetaEstado("en_duda"), "En duda");
  assert.equal(Revision.etiquetaEstado("estado_raro"), "estado_raro");
});

// --- R11 · las acciones de cada estado -------------------------------------------

test("f038 R11: accionesDe da solo las acciones de cada estado (_PERMITIDAS)", () => {
  assert.deepEqual(Revision.accionesDe("nueva"), ["editar", "descartar", "aprobar"]);
  assert.deepEqual(Revision.accionesDe("editada"), ["editar", "descartar", "aprobar"]);
  assert.deepEqual(Revision.accionesDe("aprobada"), ["editar", "descartar"], "una aprobada no se vuelve a aprobar");
  assert.deepEqual(Revision.accionesDe("descartada"), ["recuperar"]);
  assert.deepEqual(Revision.accionesDe("volcada"), [], "R21.6: nada sobre lo que ya está en Sigrid");
  assert.deepEqual(Revision.accionesDe("en_duda"), [], "R21.6: nada sobre lo que puede estar en Sigrid");
  assert.deepEqual(Revision.accionesDe("estado_raro"), [], "un estado que no se conoce no ofrece nada");
  assert.deepEqual(Revision.accionesDe(undefined), []);
});

test("f038 R11: lo que devuelve accionesDe es una copia: tocarla no cambia la tabla", () => {
  const acciones = Revision.accionesDe("nueva");
  acciones.push("recuperar");
  assert.deepEqual(Revision.accionesDe("nueva"), ["editar", "descartar", "aprobar"]);
});

test("f038 R11: «Aprobar» solo con motivos [] y en un estado que lo admite", () => {
  assert.equal(Revision.puedeAprobar(incidencia()), true);
  assert.equal(Revision.puedeAprobar(incidencia({ motivos_no_aprobable: ["sin_ubicacion"] })), false);
  assert.equal(Revision.puedeAprobar(incidencia({ motivos_no_aprobable: null })), false, "R12: null no habilita");
  assert.equal(Revision.puedeAprobar(incidencia({ estado: "aprobada" })), false);
  assert.equal(Revision.puedeAprobar(incidencia({ estado: "descartada" })), false);
  assert.equal(Revision.puedeAprobar(incidencia({ estado: "volcada" })), false);
  assert.equal(Revision.puedeAprobar(incidencia({ estado: "en_duda" })), false);
});

// --- R22 · quién, legible ----------------------------------------------------------

test("f038 R22: quienLegible: un correo tal cual, el literal del sistema con su texto", () => {
  assert.equal(Revision.quienLegible(CORREO), CORREO);
  assert.equal(
    Revision.quienLegible("sistema:normalizar_ubicacion"),
    "el sistema (ubicación puesta en el texto exacto de Sigrid)",
  );
  assert.equal(Revision.quienLegible("sistema:otra_cosa"), "el sistema");
  assert.equal(Revision.quienLegible(null), "");
  assert.equal(Revision.quienLegible(undefined), "");
  assert.equal(Revision.quienLegible(""), "");
});

// --- R4, R8 · la fecha de Madrid ----------------------------------------------------

test("f038 R4/R8: fechaDeMadrid da dd/mm/aaaa hh:mm en hora de Madrid", () => {
  // Verano (UTC+2): las 23:30 UTC son la 01:30 del día siguiente en Madrid.
  assert.equal(Revision.fechaDeMadrid("2026-07-15T23:30:00.000000+00:00"), "16/07/2026 01:30");
  // Invierno (UTC+1), con microsegundos como los manda el backend.
  assert.equal(Revision.fechaDeMadrid("2026-01-15T10:05:09.123456+00:00"), "15/01/2026 11:05");
  assert.equal(Revision.fechaDeMadrid("2026-01-15T10:05:00Z"), "15/01/2026 11:05");
  // Con el desfase de Madrid escrito.
  assert.equal(Revision.fechaDeMadrid("2026-07-16T01:30:00+02:00"), "16/07/2026 01:30");
});

test("f038 R4/R8: fechaDeMadrid con algo que no es una fecha da vacío, sin romper", () => {
  assert.equal(Revision.fechaDeMadrid(null), "");
  assert.equal(Revision.fechaDeMadrid(undefined), "");
  assert.equal(Revision.fechaDeMadrid("no es una fecha"), "");
  assert.equal(Revision.fechaDeMadrid("2026-02-30T10:00:00+00:00"), "");
});

test("f038 R4/R8: fechaDeMadrid no depende de la zona del proceso", () => {
  const antes = process.env.TZ;
  try {
    for (const zona of ["UTC", "America/New_York", "Asia/Tokyo"]) {
      process.env.TZ = zona;
      assert.equal(Revision.fechaDeMadrid("2026-07-15T23:30:00+00:00"), "16/07/2026 01:30", zona);
    }
  } finally {
    if (antes === undefined) {
      delete process.env.TZ;
    } else {
      process.env.TZ = antes;
    }
  }
});

// --- R4 (b) · «duplicada de la fila N» ----------------------------------------------

test("f038 R4 (b): duplicada de la fila N con la original cargada", () => {
  const original = incidencia({ incidencia_id: ID_1, fila_origen: 7 });
  const copia = incidencia({ incidencia_id: ID_2, fila_origen: 9, duplicada_de: ID_1 });
  assert.equal(Revision.duplicadaDe(copia, [original, copia]), "duplicada de la fila 7");
});

test("f038 R4 (b): sin la original cargada, «duplicada de otra fila del mismo fichero»", () => {
  const copia = incidencia({ incidencia_id: ID_2, fila_origen: 9, duplicada_de: ID_FUERA });
  assert.equal(Revision.duplicadaDe(copia, [copia]), "duplicada de otra fila del mismo fichero");
  assert.equal(Revision.duplicadaDe(copia, []), "duplicada de otra fila del mismo fichero");
  // La original cargada pero sin fila de origen: tampoco hay N que decir.
  const sinFila = incidencia({ incidencia_id: ID_FUERA, fila_origen: null });
  assert.equal(Revision.duplicadaDe(copia, [sinFila, copia]), "duplicada de otra fila del mismo fichero");
});

test("f038 R4 (b): una que no es duplicada no dice nada", () => {
  assert.equal(Revision.duplicadaDe(incidencia(), [incidencia()]), null);
});

// --- R4 · la fila lista para pintar ------------------------------------------------

test("f038 R4: presentarRevision da cada fila con unidad, ubicación, oficio, proveedor, urgencia y estado", () => {
  const vista = Revision.presentarRevision(respuesta());
  assert.equal(vista.obra, "9901");
  const fila = vista.filas[0];
  assert.equal(fila.incidencia_id, ID_1);
  assert.equal(fila.unidad, "U-01 · Unidad Ejemplo Uno");
  assert.equal(fila.ubicacion, "Cocina ejemplo");
  assert.equal(fila.descripcionCorta, "Grieta de ejemplo en el alicatado");
  assert.equal(fila.oficio, "9001 · Fontaneria ejemplo A");
  assert.equal(fila.proveedor, "P-01 · Proveedor Ejemplo Uno");
  assert.equal(fila.urgencia, "Normal", "la etiqueta del catálogo, no el código");
  assert.equal(fila.estado, "nueva");
  assert.equal(fila.etiquetaEstado, "Nueva");
  assert.deepEqual(fila.acciones, ["editar", "descartar", "aprobar"]);
  assert.equal(fila.aprobable, true);
  assert.equal(fila.duplicada, null);
  assert.equal(fila.revisadoPor, null, "sin revisiones no hay línea de quién");
});

test("f038 R4: el oficio dice «sin elegir: varios códigos en la obra» o «sin oficio»", () => {
  const ambigua = Revision.presentarRevision(respuesta({ incidencias: [incidencia({ vigentes: valoresAmbiguos() })] }));
  assert.match(ambigua.filas[0].oficio, /sin elegir: varios códigos en la obra/);
  assert.match(ambigua.filas[0].oficio, /Fontaneria ejemplo/);
  assert.equal(ambigua.filas[0].proveedor, "sin proveedor");

  const sinOficio = Revision.presentarRevision(
    respuesta({
      incidencias: [incidencia({ vigentes: valores({ oficio_codigo: null, oficio_nombre: null, proveedor_codigo: null, proveedor_nombre: null }) })],
    }),
  );
  assert.equal(sinOficio.filas[0].oficio, "sin oficio");
});

test("f038 R4: la descripción corta se recorta con «…» y la larga sigue entera", () => {
  const larga = "Ejemplo ".repeat(30).trim();
  const fila = Revision.presentarRevision(
    respuesta({ incidencias: [incidencia({ vigentes: valores({ descripcion: larga }) })] }),
  ).filas[0];
  assert.ok(fila.descripcionCorta.length <= 81, fila.descripcionCorta);
  assert.ok(fila.descripcionCorta.endsWith("…"));
  assert.equal(fila.descripcion, larga);
});

test("f038 R4 (b): en la lista, la duplicada dice su fila si la original está cargada", () => {
  const vista = Revision.presentarRevision(
    respuesta({
      incidencias: [
        incidencia({ incidencia_id: ID_1, fila_origen: 4 }),
        incidencia({ incidencia_id: ID_2, fila_origen: 5, duplicada_de: ID_1, motivos_no_aprobable: ["duplicada"] }),
        incidencia({ incidencia_id: ID_3, fila_origen: 6, duplicada_de: ID_FUERA, motivos_no_aprobable: ["duplicada"] }),
      ],
    }),
  );
  assert.equal(vista.filas[1].duplicada, "duplicada de la fila 4");
  assert.equal(vista.filas[2].duplicada, "duplicada de otra fila del mismo fichero");
});

test("f038 R4/R8 D-8: quien revisó por última vez, «<acción> por <correo> el <fecha>»", () => {
  const filas = Revision.presentarRevision(
    respuesta({
      incidencias: [
        incidencia({ incidencia_id: ID_1, estado: "aprobada", revision_id: 3, revisado_por: CORREO, revisado_at_utc: "2026-10-20T08:00:00.000000+00:00" }),
        incidencia({ incidencia_id: ID_2, estado: "descartada", revision_id: 4, revisado_por: OTRO_CORREO, revisado_at_utc: "2026-10-20T09:00:00.000000+00:00", motivos_no_aprobable: null }),
        incidencia({ incidencia_id: ID_3, estado: "editada", revision_id: 5, revisado_por: "sistema:normalizar_ubicacion", revisado_at_utc: "2026-10-20T10:00:00.000000+00:00" }),
      ],
    }),
  ).filas;
  assert.equal(filas[0].revisadoPor, `Aprobada por ${CORREO} el 20/10/2026 10:00`);
  assert.equal(filas[1].revisadoPor, `Descartada por ${OTRO_CORREO} el 20/10/2026 11:00`);
  assert.equal(
    filas[2].revisadoPor,
    "Revisada por el sistema (ubicación puesta en el texto exacto de Sigrid) el 20/10/2026 12:00",
    "R22: el literal del sistema no se enseña tal cual",
  );
});

test("f038 R4 D-8: el verbo de la línea se deduce del estado, en los seis (decisión 2, aceptada)", () => {
  // C-B1-3 (review del Bloque 1). Aprobada en `aprobada`, `volcada` y `en_duda`
  // (su última revisión es un `aprobar`); Descartada en `descartada`; Revisada
  // en `nueva` y `editada` (una `nueva` con revisión es la que se recuperó o se
  // editó de vuelta a lo importado: el verbo exacto, en el historial).
  const esperado = {
    nueva: "Revisada",
    editada: "Revisada",
    aprobada: "Aprobada",
    descartada: "Descartada",
    volcada: "Aprobada",
    en_duda: "Aprobada",
  };
  assert.deepEqual(Object.keys(esperado), Revision.ESTADOS, "los seis, ni uno menos");
  for (const estado of Revision.ESTADOS) {
    const fila = incidencia({
      estado: estado,
      revision_id: 9,
      revisado_por: CORREO,
      revisado_at_utc: "2026-10-20T08:00:00.000000+00:00",
    });
    assert.equal(Revision.lineaDeRevision(fila), `${esperado[estado]} por ${CORREO} el 20/10/2026 10:00`, estado);
    const vista = Revision.presentarRevision(respuesta({ incidencias: [fila] })).filas[0];
    assert.equal(vista.revisadoPor, `${esperado[estado]} por ${CORREO} el 20/10/2026 10:00`, estado);
  }
});

test("f038 R4 D-8: sin revisado_at_utc no hay línea de quién, en ninguno de los seis estados", () => {
  for (const estado of Revision.ESTADOS) {
    const fila = incidencia({ estado: estado, revision_id: null, revisado_por: null, revisado_at_utc: null });
    assert.equal(Revision.lineaDeRevision(fila), null, estado);
    assert.equal(Revision.presentarRevision(respuesta({ incidencias: [fila] })).filas[0].revisadoPor, null, estado);
  }
});

test("f038 R12: motivos null en la fila → «recarga para ver si se puede aprobar», no «Aprobar»", () => {
  const fila = Revision.presentarRevision(
    respuesta({ incidencias: [incidencia({ estado: "editada", motivos_no_aprobable: null, revision_id: 2 })] }),
  ).filas[0];
  assert.equal(fila.aprobable, false);
  assert.match(fila.avisoAprobar, /recarga para ver si se puede aprobar/i);
  assert.deepEqual(fila.motivos, []);
});

test("f038 R11/R21.6: una incidencia con `volcado` se pinta igual, sin acciones si está volcada", () => {
  // Que el objeto no rompe la fila y que una volcada no ofrece nada. La línea
  // del volcado (R21.1-R21.3), en «R21 · la presentación del volcado».
  const volcado = {
    estado: "volcada",
    sigrid_cod: "RS99.01/0001",
    volcado_at_utc: "2026-10-20T08:00:00.000000+00:00",
    volcado_por: CORREO,
    motivo: null,
  };
  const fila = Revision.presentarRevision(
    respuesta({ incidencias: [incidencia({ estado: "volcada", volcado: volcado, revision_id: 3 })] }),
  ).filas[0];
  assert.equal(fila.etiquetaEstado, "Volcada a Sigrid");
  assert.deepEqual(fila.acciones, []);
  assert.equal(fila.aprobable, false);
});

// --- R21 · la presentación del volcado (Bloque 1 ter, Q-6) ----------------------------
//
// El objeto `volcado` es el de `volcado_de` (`interface_adapters/api/volcado.py`):
// `null` o `{estado, sigrid_cod, volcado_at_utc, volcado_por, motivo}`, con
// `estado` `volcada`, `en_duda`, `rechazado` o `no_procesado`. Códigos de
// parte inventados no; los quince son los de `azure-apps/sigrid_api.md` §8.9.

/** Un objeto `volcado` de mentira: `RS99.99/NNNN`, correo de ejemplo. */
function objetoVolcado(cambios) {
  return Object.assign(
    {
      estado: "volcada",
      sigrid_cod: "RS99.99/0001",
      volcado_at_utc: "2026-10-20T08:00:00.000000+00:00",
      volcado_por: CORREO,
      motivo: null,
    },
    cambios || {},
  );
}

/** R21.4 · los quince códigos de parte de `POST /api/sigrid/partes-reclamacion` (§8.9), en su orden, con su texto. */
const TEXTOS_DE_PARTE = [
  ["referencia_no_permitida", "Sigrid no admite la referencia del parte"],
  ["referencia_duplicada_en_lote", "La referencia del parte iba repetida en el mismo envío"],
  ["referencia_en_conflicto", "En Sigrid ya hay un parte con esa referencia que no casa (de otra unidad, sin ficha o repetido)"],
  ["unidad_postventa_no_encontrada", "La unidad no está en la obra en Sigrid"],
  ["tipo_no_valido", "El tipo de reclamación no existe en Sigrid"],
  ["clase_no_valida", "La clase de reclamación no existe en Sigrid"],
  ["oficio_no_esta_en_la_obra", "El oficio no está en la obra en Sigrid"],
  ["interviniente_no_esta_en_la_obra", "El oficio y el proveedor no están juntos en la obra en Sigrid"],
  ["interviniente_ambiguo", "El oficio tiene varios proveedores en la obra: hay que elegir uno"],
  ["interviniente_repetido", "El mismo oficio y proveedor iban dos veces en el parte"],
  ["numeracion_agotada", "Se ha agotado la numeración de partes en Sigrid"],
  ["colision_de_clave", "Sigrid estaba creando otro parte a la vez: se puede volver a mandar sin riesgo"],
  ["filas_afectadas_inesperadas", "Sigrid no escribió las filas que se esperaban; el parte no se creó"],
  ["error_de_escritura", "Sigrid dio un error al escribir el parte; no se creó"],
  ["presupuesto_de_tiempo_agotado", "Se acabó el tiempo antes de llegar a este parte: se puede volver a mandar sin riesgo"],
];

const FECHA_DEL_VOLCADO = "20/10/2026 10:00"; // 08:00 UTC, en hora de verano de Madrid
const LINEA_EN_DUDA =
  "Se mandó a Sigrid el " + FECHA_DEL_VOLCADO + " por " + CORREO +
  " y no consta si se creó: volver a ensayar y volcar lo aclara sin duplicar";

test("f038 R21.4: textoMotivoVolcado da el texto de cada uno de los quince códigos de parte de §8.9", () => {
  assert.deepEqual(Revision.MOTIVOS_DE_VOLCADO, TEXTOS_DE_PARTE.map(([codigo]) => codigo));
  for (const [codigo, texto] of TEXTOS_DE_PARTE) {
    assert.equal(Revision.textoMotivoVolcado(codigo), texto, codigo);
  }
  assert.equal(new Set(TEXTOS_DE_PARTE.map(([, texto]) => texto)).size, 15, "quince textos distintos");
});

test("f038 R21.4: un código de parte que no está en la lista se enseña tal cual; sin código, nada", () => {
  assert.equal(Revision.textoMotivoVolcado("codigo_inventado"), "codigo_inventado");
  assert.equal(Revision.textoMotivoVolcado("sin_ubicacion"), "sin_ubicacion", "los motivos de la revisión no son de parte");
  assert.equal(Revision.textoMotivoVolcado(null), "");
  assert.equal(Revision.textoMotivoVolcado(undefined), "");
});

test("f038 R21.1: una volcada: «Volcada como <sigrid_cod> por <quien> el <fecha>», en hora de Madrid", () => {
  assert.equal(
    Revision.lineaDeVolcado(objetoVolcado(), "volcada"),
    "Volcada como RS99.99/0001 por " + CORREO + " el " + FECHA_DEL_VOLCADO,
  );
  // En invierno, Madrid va una hora por delante de UTC (no dos).
  assert.equal(
    Revision.lineaDeVolcado(objetoVolcado({ sigrid_cod: "RS99.99/0002", volcado_at_utc: "2026-12-01T08:00:00+00:00", volcado_por: OTRO_CORREO }), "volcada"),
    "Volcada como RS99.99/0002 por " + OTRO_CORREO + " el 01/12/2026 09:00",
  );
});

test("f038 R21.1, R22: quien volcó pasa por quienLegible", () => {
  assert.equal(
    Revision.lineaDeVolcado(objetoVolcado({ volcado_por: "sistema:normalizar_ubicacion" }), "volcada"),
    "Volcada como RS99.99/0001 por el sistema (ubicación puesta en el texto exacto de Sigrid) el " + FECHA_DEL_VOLCADO,
  );
  assert.equal(
    Revision.lineaDeVolcado(objetoVolcado({ estado: "en_duda", sigrid_cod: null, volcado_por: "sistema:otro" }), "en_duda"),
    LINEA_EN_DUDA.replace(CORREO, "el sistema"),
  );
});

test("f038 R21.2: una en duda, sin motivo: cuándo, quién y que volver a ensayar lo aclara", () => {
  assert.equal(Revision.lineaDeVolcado(objetoVolcado({ estado: "en_duda", sigrid_cod: null }), "en_duda"), LINEA_EN_DUDA);
});

test("f038 R21.2, R21.4: una en duda con motivo lleva su texto; uno desconocido, tal cual", () => {
  assert.equal(
    Revision.lineaDeVolcado(objetoVolcado({ estado: "en_duda", sigrid_cod: null, motivo: "colision_de_clave" }), "en_duda"),
    LINEA_EN_DUDA + ". Motivo: Sigrid estaba creando otro parte a la vez: se puede volver a mandar sin riesgo",
  );
  assert.equal(
    Revision.lineaDeVolcado(objetoVolcado({ estado: "en_duda", sigrid_cod: null, motivo: "codigo_inventado" }), "en_duda"),
    LINEA_EN_DUDA + ". Motivo: codigo_inventado",
  );
});

test("f038 R21.3: el último intento rechazado o no procesado de una aprobada, con su motivo", () => {
  assert.equal(
    Revision.lineaDeVolcado(objetoVolcado({ estado: "rechazado", sigrid_cod: null, motivo: "oficio_no_esta_en_la_obra" }), "aprobada"),
    "Último intento de volcado: no se creó el " + FECHA_DEL_VOLCADO + " por " + CORREO + ": El oficio no está en la obra en Sigrid",
  );
  assert.equal(
    Revision.lineaDeVolcado(objetoVolcado({ estado: "no_procesado", sigrid_cod: null, motivo: "presupuesto_de_tiempo_agotado" }), "aprobada"),
    "Último intento de volcado: no se llegó a procesar el " + FECHA_DEL_VOLCADO + " por " + CORREO +
      ": Se acabó el tiempo antes de llegar a este parte: se puede volver a mandar sin riesgo",
  );
  assert.equal(
    Revision.lineaDeVolcado(objetoVolcado({ estado: "rechazado", sigrid_cod: null, motivo: "codigo_inventado" }), "aprobada"),
    "Último intento de volcado: no se creó el " + FECHA_DEL_VOLCADO + " por " + CORREO + ": codigo_inventado",
  );
  assert.equal(
    Revision.lineaDeVolcado(objetoVolcado({ estado: "rechazado", sigrid_cod: null, motivo: null }), "aprobada"),
    "Último intento de volcado: no se creó el " + FECHA_DEL_VOLCADO + " por " + CORREO,
    "sin motivo, sin «: »",
  );
  // C-B1t-2 · un lote rechazado entero deja cada parte `no_procesado` con el
  // CÓDIGO DE LOTE de §8.9 como motivo (`todos_no_procesados`): hoy sale tal
  // cual, como cualquier código que no es de parte (R21.4; O-B1t-1, abierta).
  assert.equal(
    Revision.lineaDeVolcado(objetoVolcado({ estado: "no_procesado", sigrid_cod: null, motivo: "obra_no_encontrada" }), "aprobada"),
    "Último intento de volcado: no se llegó a procesar el " + FECHA_DEL_VOLCADO + " por " + CORREO + ": obra_no_encontrada",
  );
});

test("f038 R21.3: el último intento sale en cualquier estado que no sea volcada ni en duda", () => {
  const rechazado = objetoVolcado({ estado: "rechazado", sigrid_cod: null, motivo: "error_de_escritura" });
  for (const estado of ["nueva", "editada", "aprobada", "descartada"]) {
    assert.match(Revision.lineaDeVolcado(rechazado, estado), /^Último intento de volcado: no se creó /, estado);
  }
  for (const estado of ["volcada", "en_duda"]) {
    assert.equal(Revision.lineaDeVolcado(rechazado, estado), null, estado);
    assert.equal(Revision.lineaDeVolcado(Object.assign({}, rechazado, { estado: "no_procesado" }), estado), null, estado);
  }
});

test("f038 R21: sin objeto volcado, o con un estado del volcado desconocido, no hay línea", () => {
  for (const estado of Revision.ESTADOS) {
    assert.equal(Revision.lineaDeVolcado(null, estado), null, estado);
    assert.equal(Revision.lineaDeVolcado(undefined, estado), null, estado);
    assert.equal(Revision.lineaDeVolcado(objetoVolcado({ estado: "previsto" }), estado), null, estado);
  }
});

test("f038 R21.1-R21.3, R21.6: presentarRevision da la línea del volcado y «Ya no se revisa aquí»", () => {
  const filas = Revision.presentarRevision(
    respuesta({
      incidencias: [
        incidencia({ incidencia_id: ID_1, estado: "volcada", volcado: objetoVolcado() }),
        incidencia({ incidencia_id: ID_2, estado: "en_duda", volcado: objetoVolcado({ estado: "en_duda", sigrid_cod: null }) }),
        incidencia({
          incidencia_id: ID_3,
          estado: "aprobada",
          volcado: objetoVolcado({ estado: "rechazado", sigrid_cod: null, motivo: "numeracion_agotada" }),
        }),
        incidencia({ incidencia_id: ID_4, estado: "nueva" }),
      ],
    }),
  ).filas;
  assert.deepEqual(
    filas.map((f) => [f.etiquetaEstado, f.yaNoSeRevisa, f.lineaVolcado]),
    [
      ["Volcada a Sigrid", "Ya no se revisa aquí", "Volcada como RS99.99/0001 por " + CORREO + " el " + FECHA_DEL_VOLCADO],
      ["En duda", "Ya no se revisa aquí", LINEA_EN_DUDA],
      ["Aprobada", "", "Último intento de volcado: no se creó el " + FECHA_DEL_VOLCADO + " por " + CORREO + ": Se ha agotado la numeración de partes en Sigrid"],
      ["Nueva", "", null],
    ],
  );
  assert.deepEqual(filas.map((f) => f.acciones.length), [0, 0, 2, 3], "R21.6: ni una acción en volcada ni en duda");
});

test("f038 R21.6: «Ya no se revisa aquí» va con volcada y en duda aunque no traigan objeto, y con ningún otro estado", () => {
  for (const estado of Revision.ESTADOS) {
    const fila = Revision.presentarRevision(respuesta({ incidencias: [incidencia({ estado: estado })] })).filas[0];
    assert.equal(fila.yaNoSeRevisa, ["volcada", "en_duda"].includes(estado) ? "Ya no se revisa aquí" : "", estado);
  }
});

// --- R5 · el resumen de toda la obra -------------------------------------------------

test("f038 R5: el resumen sale del de la respuesta: seis estados y nueve motivos con su texto", () => {
  const vista = Revision.presentarResumen(resumen());
  assert.equal(vista.total, 10);
  assert.equal(vista.aprobadas, 1);
  assert.equal(vista.conMotivos, 3);
  assert.deepEqual(
    vista.porEstado.map((e) => [e.estado, e.etiqueta, e.n]),
    [
      ["nueva", "Nueva", 4],
      ["editada", "Editada", 2],
      ["aprobada", "Aprobada", 1],
      ["descartada", "Descartada", 1],
      ["volcada", "Volcada a Sigrid", 1],
      ["en_duda", "En duda", 1],
    ],
  );
  assert.deepEqual(vista.porMotivo.map((m) => m.motivo), Revision.MOTIVOS);
  assert.equal(vista.porMotivo[1].texto, "Falta la ubicación");
  assert.equal(vista.porMotivo[1].n, 2);
});

test("f038 R5: un motivo del resumen que no se conoce sale tal cual, al final", () => {
  const vista = Revision.presentarResumen(
    resumen({ por_motivo: Object.assign({}, resumen().por_motivo, { motivo_nuevo: 3 }) }),
  );
  const ultimo = vista.porMotivo[vista.porMotivo.length - 1];
  assert.deepEqual([ultimo.motivo, ultimo.texto, ultimo.n], ["motivo_nuevo", "motivo_nuevo", 3]);
});

test("f038 R5: sin resumen no hay nada que pintar", () => {
  assert.equal(Revision.presentarResumen(null), null);
  assert.equal(Revision.presentarResumen(undefined), null);
});

// --- R3, R6, R7 · la consulta y la paginación ---------------------------------------

test("f038 R3/R6: consultaDe sin filtros pide la obra con «activas» por defecto, sin tamano", () => {
  assert.deepEqual(Revision.consultaDe(" 9901 ", {}, null), { obra: "9901", estado: "activas" });
  assert.deepEqual(Revision.consultaDe("9901", undefined), { obra: "9901", estado: "activas" });
});

test("f038 R6: consultaDe con un estado de la lista y «solo lo que tiene algo que corregir»", () => {
  for (const estado of ["activas", "todas", "nueva", "editada", "aprobada", "descartada"]) {
    assert.deepEqual(Revision.consultaDe("9901", { estado: estado }), { obra: "9901", estado: estado });
  }
  assert.deepEqual(Revision.consultaDe("9901", { estado: "nueva", conMotivos: true }), {
    obra: "9901",
    estado: "nueva",
    con_motivos: true,
  });
  // `false` es «no filtrar», no «solo las que no tienen»: la clave no viaja.
  assert.deepEqual(Revision.consultaDe("9901", { estado: "nueva", conMotivos: false }), {
    obra: "9901",
    estado: "nueva",
  });
});

test("f038 R6: un estado que no está en el selector cae en «activas»", () => {
  assert.deepEqual(Revision.consultaDe("9901", { estado: "inventado" }), { obra: "9901", estado: "activas" });
  assert.deepEqual(Revision.FILTROS_DE_ESTADO.slice(0, 6), ["activas", "todas", "nueva", "editada", "aprobada", "descartada"]);
  assert.equal(Revision.FILTROS_DE_ESTADO[0], "activas", "el primero es el de por defecto");
});

test("f038 R21.5: consultaDe lleva también los filtros volcada y en_duda; el selector tiene los ocho", () => {
  for (const estado of ["volcada", "en_duda"]) {
    assert.deepEqual(Revision.consultaDe("9901", { estado: estado }), { obra: "9901", estado: estado });
  }
  assert.deepEqual(Revision.FILTROS_DE_ESTADO, [
    "activas", "todas", "nueva", "editada", "aprobada", "descartada", "volcada", "en_duda",
  ]);
});

test("f038 R21.5: el componente pide la primera página con el filtro volcada o en_duda tal cual", async () => {
  for (const estado of ["volcada", "en_duda"]) {
    const { app, llamadas } = componente();
    await app.iniciar();
    app.obra = "9901";
    app.filtros.estado = estado;
    await app.cambiarFiltro();
    const pedidas = llamadas.filter((l) => l.nombre === "revision");
    assert.equal(pedidas.length, 1, estado);
    assert.deepEqual(pedidas[0].args, ["9901", { estado: estado, con_motivos: undefined }, undefined], estado);
  }
});

test("f038 R7: consultaDe lleva el cursor tal cual, sin decodificarlo ni construirlo", () => {
  const cursor = "eyJjIjoiMjAyNi0xMC0yMFQwODowMDowMCswMDowMCIsImYiOjIsImkiOiJ4In0";
  assert.deepEqual(Revision.consultaDe("9901", { estado: "todas" }, cursor), {
    obra: "9901",
    estado: "todas",
    cursor: cursor,
  });
  assert.deepEqual(Revision.consultaDe("9901", {}, ""), { obra: "9901", estado: "activas" });
  assert.equal("tamano" in Revision.consultaDe("9901", {}, cursor), false, "R7: la página no manda tamano");
});

test("f038 R7: anadirPagina añade sin repetir por incidencia_id y da «N de M»", () => {
  const primera = Revision.anadirPagina([], respuesta({
    incidencias: [incidencia({ incidencia_id: ID_1 }), incidencia({ incidencia_id: ID_2 })],
    total_filtrado: 4,
    siguiente: "cursor-inventado-1",
  }));
  assert.deepEqual(primera.incidencias.map((i) => i.incidencia_id), [ID_1, ID_2]);
  assert.equal(primera.siguiente, "cursor-inventado-1");
  assert.equal(primera.cargadas, 2);
  assert.equal(primera.total, 4);
  assert.equal(primera.nDeM, "2 de 4");

  // Una fila que cambió de estado entre páginas puede volver a salir: no se repite.
  const segunda = Revision.anadirPagina(primera.incidencias, respuesta({
    incidencias: [incidencia({ incidencia_id: ID_2 }), incidencia({ incidencia_id: ID_3 }), incidencia({ incidencia_id: ID_4 })],
    total_filtrado: 4,
    siguiente: null,
  }));
  assert.deepEqual(segunda.incidencias.map((i) => i.incidencia_id), [ID_1, ID_2, ID_3, ID_4]);
  assert.equal(segunda.siguiente, null, "con siguiente: null no hay «Cargar más»");
  assert.equal(segunda.nDeM, "4 de 4");
});

test("f038 R7: anadirPagina no toca la lista que recibe", () => {
  const cargadas = [incidencia({ incidencia_id: ID_1 })];
  Revision.anadirPagina(cargadas, respuesta({ incidencias: [incidencia({ incidencia_id: ID_2 })] }));
  assert.equal(cargadas.length, 1);
});

test("f038 R7: anadirPagina sin siguiente, o con algo que no es un cursor, da null", () => {
  assert.equal(Revision.anadirPagina([], respuesta({ siguiente: undefined })).siguiente, null);
  assert.equal(Revision.anadirPagina([], respuesta({ siguiente: "" })).siguiente, null);
  assert.equal(Revision.anadirPagina([], respuesta({ siguiente: 7 })).siguiente, null);
});

// --- R12 · ajustar el resumen tras una acción -----------------------------------------

test("f038 R12: ajustarResumen tras aprobar mueve el estado y deja los motivos", () => {
  const antes = incidencia({ estado: "editada", motivos_no_aprobable: [] });
  const despues = incidencia({ estado: "aprobada", motivos_no_aprobable: [] });
  const ajustado = Revision.ajustarResumen(resumen(), antes, despues);
  assert.equal(ajustado.por_estado.editada, 1);
  assert.equal(ajustado.por_estado.aprobada, 2);
  assert.equal(ajustado.total, 10, "el total de la obra no cambia");
  assert.equal(ajustado.con_motivos, 3);
});

test("f038 R12: ajustarResumen tras editar mueve el estado y los motivos (uno quita, otro pone)", () => {
  const antes = incidencia({ estado: "nueva", motivos_no_aprobable: ["sin_ubicacion", "oficio_ambiguo"] });
  const despues = incidencia({ estado: "editada", motivos_no_aprobable: ["ubicacion_fuera_de_lista"] });
  const ajustado = Revision.ajustarResumen(resumen(), antes, despues);
  assert.equal(ajustado.por_estado.nueva, 3);
  assert.equal(ajustado.por_estado.editada, 3);
  assert.equal(ajustado.por_motivo.sin_ubicacion, 1);
  assert.equal(ajustado.por_motivo.oficio_ambiguo, 0);
  assert.equal(ajustado.por_motivo.ubicacion_fuera_de_lista, 2);
  assert.equal(ajustado.con_motivos, 3, "seguía con motivos y sigue con motivos");
});

test("f038 R12: ajustarResumen: una edición que lo arregla todo baja «con algo que corregir»", () => {
  const antes = incidencia({ estado: "nueva", motivos_no_aprobable: ["sin_ubicacion"] });
  const despues = incidencia({ estado: "editada", motivos_no_aprobable: [] });
  const ajustado = Revision.ajustarResumen(resumen(), antes, despues);
  assert.equal(ajustado.con_motivos, 2);
  assert.equal(ajustado.por_motivo.sin_ubicacion, 1);
});

test("f038 R12: ajustarResumen tras descartar o recuperar (motivos null) solo mueve estados", () => {
  const antes = incidencia({ estado: "nueva", motivos_no_aprobable: ["sin_ubicacion"] });
  const descartada = incidencia({ estado: "descartada", motivos_no_aprobable: null });
  const tras = Revision.ajustarResumen(resumen(), antes, descartada);
  assert.equal(tras.por_estado.nueva, 3);
  assert.equal(tras.por_estado.descartada, 2);
  assert.deepEqual(tras.por_motivo, resumen().por_motivo, "los motivos se quedan como estaban");
  assert.equal(tras.con_motivos, 3);

  const recuperada = incidencia({ estado: "editada", motivos_no_aprobable: null });
  const otra = Revision.ajustarResumen(tras, descartada, recuperada);
  assert.equal(otra.por_estado.descartada, 1);
  assert.equal(otra.por_estado.editada, 3);
  assert.deepEqual(otra.por_motivo, resumen().por_motivo);
});

test("f038 R12: ajustarResumen no toca el resumen que recibe", () => {
  const original = resumen();
  Revision.ajustarResumen(original, incidencia({ estado: "nueva" }), incidencia({ estado: "aprobada" }));
  assert.deepEqual(original, resumen());
});

test("f038 R12: ajustarResumen sin resumen devuelve lo que había", () => {
  assert.equal(Revision.ajustarResumen(null, incidencia(), incidencia()), null);
});

// --- R8 · el detalle: «llegó así» y el historial -----------------------------------------

test("f038 R8: el detalle da los vigentes y, en cada campo de `cambios`, lo importado", () => {
  const detalle = Revision.detalleDe(
    incidencia({
      importados: valores({ ubicacion: null, descripcion: "Grieta  de   ejemplo" }),
      vigentes: valores({ ubicacion: "Baño ejemplo", descripcion: "Grieta de ejemplo" }),
      cambios: ["ubicacion", "descripcion"],
    }),
    catalogo(),
  );
  assert.deepEqual(detalle.map((c) => c.campo), ["unidad", "ubicacion", "descripcion", "detalle", "oficio", "proveedor", "urgencia", "listado"]);
  const ubicacion = detalle.find((c) => c.campo === "ubicacion");
  assert.equal(ubicacion.valor, "Baño ejemplo");
  assert.equal(ubicacion.llegoAsi, "llegó así: sin ubicación");
  const descripcion = detalle.find((c) => c.campo === "descripcion");
  assert.equal(descripcion.llegoAsi, "llegó así: Grieta  de   ejemplo");
  assert.equal(detalle.find((c) => c.campo === "unidad").llegoAsi, null, "lo que no cambió no dice nada");
  assert.equal(detalle.find((c) => c.campo === "urgencia").valor, "Normal");
});

test("f038 R8/R22: el historial con fecha de Madrid, acción, quién, campos y motivo", () => {
  const vista = Revision.presentarHistorial({
    incidencia_id: ID_1,
    importada: { origen: "excel", importacion_id: null, creada_at_utc: "2026-10-19T07:00:00.000000+00:00" },
    revisiones: [
      { revision_id: 1, accion: "editar", revisado_at_utc: "2026-10-19T08:00:00.000000+00:00", correo: "sistema:normalizar_ubicacion", campos_cambiados: ["ubicacion"], motivo: null },
      { revision_id: 2, accion: "editar", revisado_at_utc: "2026-10-20T08:00:00.000000+00:00", correo: CORREO, campos_cambiados: ["oficio", "proveedor"], motivo: null },
      { revision_id: 3, accion: "descartar", revisado_at_utc: "2026-10-20T09:00:00.000000+00:00", correo: OTRO_CORREO, campos_cambiados: [], motivo: "Repetida, de ejemplo" },
      { revision_id: 4, accion: "recuperar", revisado_at_utc: "2026-10-20T09:30:00.000000+00:00", correo: CORREO, campos_cambiados: [], motivo: null },
      { revision_id: 5, accion: "aprobar", revisado_at_utc: "2026-10-20T10:00:00.000000+00:00", correo: CORREO, campos_cambiados: [], motivo: null },
    ],
  });
  assert.equal(vista.importada, "19/10/2026 09:00");
  assert.deepEqual(
    vista.revisiones.map((r) => [r.fecha, r.accion, r.quien]),
    [
      ["19/10/2026 10:00", "Editada", "el sistema (ubicación puesta en el texto exacto de Sigrid)"],
      ["20/10/2026 10:00", "Editada", CORREO],
      ["20/10/2026 11:00", "Descartada", OTRO_CORREO],
      ["20/10/2026 11:30", "Recuperada", CORREO],
      ["20/10/2026 12:00", "Aprobada", CORREO],
    ],
  );
  assert.deepEqual(vista.revisiones[1].campos, ["Oficio", "Proveedor"]);
  assert.equal(vista.revisiones[2].motivo, "Repetida, de ejemplo");
  assert.equal(vista.revisiones[0].motivo, "");
});

test("f038 R8: un historial vacío o sin respuesta no rompe", () => {
  assert.deepEqual(Revision.presentarHistorial(null).revisiones, []);
  assert.deepEqual(Revision.presentarHistorial({ incidencia_id: ID_1, revisiones: [] }).revisiones, []);
});

// --- R9 · el formulario ------------------------------------------------------------------

test("f038 R9: ubicacionesDe da solo las de la unidad elegida; sin lista, ninguna", () => {
  assert.deepEqual(Revision.ubicacionesDe(catalogo(), "U-01"), ["Cocina ejemplo", "Baño ejemplo"]);
  assert.deepEqual(Revision.ubicacionesDe(catalogo(), "U-02"), ["Cocina ejemplo", "Terraza ejemplo"]);
  assert.deepEqual(Revision.ubicacionesDe(catalogo(), "U-03"), [], "una unidad con lista vacía no ofrece ninguna");
  assert.deepEqual(Revision.ubicacionesDe(catalogo(), "U-99"), []);
  assert.deepEqual(Revision.ubicacionesDe({}, "U-01"), []);
  assert.deepEqual(Revision.ubicacionesDe(null, "U-01"), []);
});

test("f038 R9: al cambiar la unidad, una ubicación que también es de la nueva se conserva", () => {
  const formulario = Revision.formularioDe(valores({ ubicacion: "Cocina ejemplo" }), catalogo());
  formulario.unidad_codigo = "U-02";
  const nuevo = Revision.alCambiarUnidad(formulario, catalogo());
  assert.equal(nuevo.ubicacion, "Cocina ejemplo");
  assert.equal(nuevo.aviso, "");
});

test("f038 R9: al cambiar la unidad, una ubicación que no es de la nueva se vacía con aviso", () => {
  const formulario = Revision.formularioDe(valores({ ubicacion: "Baño ejemplo" }), catalogo());
  formulario.unidad_codigo = "U-02";
  const nuevo = Revision.alCambiarUnidad(formulario, catalogo());
  assert.equal(nuevo.ubicacion, "");
  assert.match(nuevo.aviso, /esta ubicación no es de la nueva unidad/i);
  assert.equal(formulario.ubicacion, "Baño ejemplo", "no muta el formulario que recibe");
});

test("f038 R9: la comparación de la ubicación es exacta: una mayúscula de diferencia no se conserva", () => {
  const formulario = Revision.formularioDe(valores({ unidad_codigo: "U-01", ubicacion: "Cocina ejemplo" }), catalogo());
  formulario.unidad_codigo = "U-02";
  const cat = catalogo();
  cat.ubicaciones["U-02"] = ["cocina ejemplo"];
  assert.equal(Revision.alCambiarUnidad(formulario, cat).ubicacion, "");
});

test("f038 R9: al cambiar a una unidad sin lista, la ubicación se vacía", () => {
  const formulario = Revision.formularioDe(valores(), catalogo());
  formulario.unidad_codigo = "U-03";
  assert.equal(Revision.alCambiarUnidad(formulario, catalogo()).ubicacion, "");
});

test("f038 R9 (b): con el oficio ambiguo, los del grupo de la fila (por grupo.etiqueta) van primero", () => {
  const opciones = Revision.opcionesDeOficio(catalogo(), valoresAmbiguos());
  assert.deepEqual(opciones.map((o) => o.codigo), ["9001", "9002", "9003", "9004"]);
  assert.deepEqual(opciones.map((o) => o.delGrupo), [true, true, false, false]);
  assert.equal(opciones[0].texto, "9001 · Fontaneria ejemplo A");
});

test("f038 R9: sin oficio ambiguo, los oficios van en el orden del catálogo, por código", () => {
  const opciones = Revision.opcionesDeOficio(catalogo(), valores());
  assert.deepEqual(opciones.map((o) => o.codigo), ["9003", "9001", "9004", "9002"]);
  assert.ok(opciones.every((o) => o.delGrupo === false));
  assert.ok(opciones.every((o) => o.fueraDeLista === false));
});

test("f038 R9 (a): los proveedores de un oficio salen de catalogo.pares; sin nombre, el código", () => {
  assert.deepEqual(Revision.proveedoresDe(catalogo(), "9001", valores()), [
    { codigo: "P-01", texto: "P-01 · Proveedor Ejemplo Uno", fueraDeLista: false },
    { codigo: "P-02", texto: "P-02", fueraDeLista: false },
  ]);
  assert.deepEqual(
    Revision.proveedoresDe(catalogo(), "9003", valores({ oficio_codigo: "9003", proveedor_codigo: "P-03", proveedor_nombre: "Proveedor Ejemplo Tres" })).map((p) => p.codigo),
    ["P-03"],
  );
  assert.deepEqual(Revision.proveedoresDe(catalogo(), "9004", valores({ oficio_codigo: "9004", proveedor_codigo: null, proveedor_nombre: null })), []);
});

test("f038 R9 (c): con el oficio ambiguo sin elegir, solo el proveedor vigente o ninguno", () => {
  const conProveedor = valoresAmbiguos({ proveedor_codigo: "P-01", proveedor_nombre: "Proveedor Ejemplo Uno" });
  assert.deepEqual(Revision.proveedoresDe(catalogo(), "", conProveedor), [
    { codigo: "P-01", texto: "P-01 · Proveedor Ejemplo Uno", fueraDeLista: false },
  ]);
  assert.deepEqual(Revision.proveedoresDe(catalogo(), "", valoresAmbiguos()), []);
  assert.deepEqual(Revision.proveedoresDe(catalogo(), null, valores({ oficio_codigo: null, oficio_nombre: null })), [], "no hay proveedor sin oficio");
});

test("f038 R9: cambiar el oficio vacía el proveedor que no casa, con aviso", () => {
  const formulario = Revision.formularioDe(valores(), catalogo());
  formulario.oficio_codigo = "9003";
  const nuevo = Revision.alCambiarOficio(formulario, catalogo());
  assert.equal(nuevo.proveedor_codigo, "");
  assert.match(nuevo.aviso, /proveedor/i);
  assert.equal(formulario.proveedor_codigo, "P-01", "no muta el formulario que recibe");
});

test("f038 R9: cambiar el oficio conserva el proveedor que también es de ese oficio", () => {
  const formulario = Revision.formularioDe(valores(), catalogo());
  formulario.oficio_codigo = "9002";
  const nuevo = Revision.alCambiarOficio(formulario, catalogo());
  assert.equal(nuevo.proveedor_codigo, "P-01");
  assert.equal(nuevo.aviso, "");
});

test("f038 R9: formularioDe da los vigentes como textos del formulario (vacío = «»)", () => {
  const formulario = Revision.formularioDe(valores({ detalle: null, urgencia: null }), catalogo());
  assert.equal(formulario.unidad_codigo, "U-01");
  assert.equal(formulario.ubicacion, "Cocina ejemplo");
  assert.equal(formulario.descripcion, "Grieta de ejemplo en el alicatado");
  assert.equal(formulario.detalle, "");
  assert.equal(formulario.oficio_codigo, "9001");
  assert.equal(formulario.proveedor_codigo, "P-01");
  assert.equal(formulario.urgencia, "");
  assert.equal(formulario.listado, "repaso");
  assert.equal(formulario.aviso, "");
});

test("f038 R9 (d): valoresDelFormulario: las ocho claves exactas; ubicación y detalle vacíos → null, nunca «»", () => {
  const formulario = Revision.formularioDe(valores(), catalogo());
  formulario.ubicacion = "";
  formulario.detalle = "   ";
  formulario.urgencia = "";
  const valoresPedidos = Revision.valoresDelFormulario(formulario);
  assert.deepEqual(Object.keys(valoresPedidos).sort(), [
    "descripcion",
    "detalle",
    "listado",
    "oficio_codigo",
    "proveedor_codigo",
    "ubicacion",
    "unidad_codigo",
    "urgencia",
  ]);
  assert.equal(valoresPedidos.ubicacion, null);
  assert.equal(valoresPedidos.detalle, null);
  assert.equal(valoresPedidos.urgencia, null);
  assert.equal(valoresPedidos.unidad_codigo, "U-01");
  assert.equal(valoresPedidos.oficio_codigo, "9001");
  assert.equal(valoresPedidos.proveedor_codigo, "P-01");
  assert.equal(valoresPedidos.listado, "repaso");
});

test("f038 R9 (c): el oficio ambiguo sin tocar viaja como oficio_codigo: null", () => {
  const formulario = Revision.formularioDe(valoresAmbiguos(), catalogo());
  assert.equal(formulario.oficio_codigo, "");
  const pedidos = Revision.valoresDelFormulario(formulario);
  assert.equal(pedidos.oficio_codigo, null);
  assert.equal(pedidos.proveedor_codigo, null);
});

test("f038 R9 (e): hayCambios con la normalización del backend", () => {
  const vigentes = valores({ detalle: "Detalle de ejemplo" });
  const formulario = Revision.formularioDe(vigentes, catalogo());
  assert.equal(Revision.hayCambios(formulario, vigentes), false, "recién abierto no hay cambios");

  formulario.descripcion = "  Grieta   de ejemplo\ten el  alicatado ";
  formulario.detalle = "  Detalle de ejemplo  ";
  assert.equal(Revision.hayCambios(formulario, vigentes), false, "solo blancos: el backend diría sin_cambios");

  formulario.descripcion = "Grieta de ejemplo en el zocalo";
  assert.equal(Revision.hayCambios(formulario, vigentes), true);
});

test("f038 R9 (e): hayCambios mira cada uno de los ocho campos", () => {
  const vigentes = valores();
  const cambios = {
    unidad_codigo: "U-02",
    ubicacion: "Baño ejemplo",
    descripcion: "Otra descripcion de ejemplo",
    detalle: "Un detalle de ejemplo",
    oficio_codigo: "9002",
    proveedor_codigo: "P-02",
    urgencia: "urgente",
    listado: "garantia",
  };
  for (const [campo, valor] of Object.entries(cambios)) {
    const formulario = Revision.formularioDe(vigentes, catalogo());
    formulario[campo] = valor;
    assert.equal(Revision.hayCambios(formulario, vigentes), true, campo);
  }
  const sinUbicacion = Revision.formularioDe(vigentes, catalogo());
  sinUbicacion.ubicacion = "";
  assert.equal(Revision.hayCambios(sinUbicacion, vigentes), true, "quitar la ubicación es un cambio");
});

test("f038 R9 (e): con el oficio ambiguo sin tocar no hay cambios", () => {
  const vigentes = valoresAmbiguos();
  assert.equal(Revision.hayCambios(Revision.formularioDe(vigentes, catalogo()), vigentes), false);
});

test("f038 R9: descripción y detalle con su contador (128 y 2000)", () => {
  assert.equal(Revision.MAX_DESCRIPCION, 128);
  assert.equal(Revision.MAX_DETALLE, 2000);
  assert.equal(Revision.MAX_MOTIVO, 500);
  assert.equal(Revision.contador("Ejemplo", 128), "7 / 128");
  assert.equal(Revision.contador(null, 2000), "0 / 2000");
});

// --- R24 · un vigente fuera del catálogo de hoy se conserva marcado --------------------------

test("f038 R24: una ubicación vigente fuera de la lista se conserva como opción marcada", () => {
  const vigentes = valores({ ubicacion: "Cocina antigua ejemplo" });
  const formulario = Revision.formularioDe(vigentes, catalogo());
  assert.equal(formulario.ubicacion, "Cocina antigua ejemplo", "no se vacía en silencio");
  assert.equal(formulario.fueraDeLista.ubicacion, true);
  const opciones = Revision.opcionesDeUbicacion(catalogo(), "U-01", vigentes);
  const marcada = opciones.find((o) => o.codigo === "Cocina antigua ejemplo");
  assert.ok(marcada, "la vigente está entre las opciones");
  assert.equal(marcada.fueraDeLista, true);
  assert.match(marcada.texto, /no está en la lista de Sigrid de hoy/);
  assert.deepEqual(opciones.filter((o) => !o.fueraDeLista).map((o) => o.codigo), ["Cocina ejemplo", "Baño ejemplo"]);
  // Sin nada fuera de lista, ninguna marca.
  assert.ok(Revision.opcionesDeUbicacion(catalogo(), "U-01", valores()).every((o) => !o.fueraDeLista));
});

test("f038 R24: cambiar la unidad sigue vaciando la ubicación conservada", () => {
  const vigentes = valores({ ubicacion: "Cocina antigua ejemplo" });
  const formulario = Revision.formularioDe(vigentes, catalogo());
  formulario.unidad_codigo = "U-02";
  const nuevo = Revision.alCambiarUnidad(formulario, catalogo());
  assert.equal(nuevo.ubicacion, "");
  assert.match(nuevo.aviso, /esta ubicación no es de la nueva unidad/i);
  // En otra unidad, la conservada ya no se ofrece.
  assert.ok(Revision.opcionesDeUbicacion(catalogo(), "U-02", vigentes).every((o) => !o.fueraDeLista));
});

test("f038 R24: una unidad vigente que ya no es de la obra se conserva marcada", () => {
  const vigentes = valores({ unidad_codigo: "U-77", unidad_nombre: "Unidad Ejemplo Vieja", ubicacion: null });
  const formulario = Revision.formularioDe(vigentes, catalogo());
  assert.equal(formulario.unidad_codigo, "U-77");
  assert.equal(formulario.fueraDeLista.unidad, true);
  const opciones = Revision.opcionesDeUnidad(catalogo(), vigentes);
  assert.deepEqual(opciones.slice(0, 3).map((o) => [o.codigo, o.fueraDeLista]), [
    ["U-01", false],
    ["U-02", false],
    ["U-03", false],
  ]);
  const marcada = opciones.find((o) => o.codigo === "U-77");
  assert.equal(marcada.fueraDeLista, true);
  assert.match(marcada.texto, /Unidad Ejemplo Vieja/);
  assert.match(marcada.texto, /no está en la lista de Sigrid de hoy/);
  assert.equal(opciones.find((o) => o.codigo === "U-03").texto, "U-03", "sin nombre, el código");
});

test("f038 R24: un oficio vigente que ya no está en la obra se conserva marcado", () => {
  const vigentes = valores({ oficio_codigo: "9077", oficio_nombre: "Oficio Ejemplo Viejo", proveedor_codigo: null, proveedor_nombre: null });
  const formulario = Revision.formularioDe(vigentes, catalogo());
  assert.equal(formulario.oficio_codigo, "9077");
  assert.equal(formulario.fueraDeLista.oficio, true);
  const marcada = Revision.opcionesDeOficio(catalogo(), vigentes).find((o) => o.codigo === "9077");
  assert.equal(marcada.fueraDeLista, true);
  assert.match(marcada.texto, /9077 · Oficio Ejemplo Viejo/);
  assert.match(marcada.texto, /no está en la lista de Sigrid de hoy/);
});

test("f038 R24: un proveedor vigente cuyo par ya no está se conserva marcado con su oficio", () => {
  const vigentes = valores({ proveedor_codigo: "P-77", proveedor_nombre: "Proveedor Ejemplo Viejo" });
  const formulario = Revision.formularioDe(vigentes, catalogo());
  assert.equal(formulario.proveedor_codigo, "P-77");
  assert.equal(formulario.fueraDeLista.proveedor, true);
  const marcada = Revision.proveedoresDe(catalogo(), "9001", vigentes).find((o) => o.codigo === "P-77");
  assert.equal(marcada.fueraDeLista, true);
  assert.match(marcada.texto, /no está en la lista de Sigrid de hoy/);
  // Con otro oficio, ya no se ofrece, y cambiar el oficio lo vacía.
  assert.equal(Revision.proveedoresDe(catalogo(), "9002", vigentes).some((o) => o.codigo === "P-77"), false);
  formulario.oficio_codigo = "9002";
  assert.equal(Revision.alCambiarOficio(formulario, catalogo()).proveedor_codigo, "");
});

test("f038 R24: lo que está en el catálogo no se marca", () => {
  const formulario = Revision.formularioDe(valores(), catalogo());
  assert.deepEqual(formulario.fueraDeLista, { unidad: false, ubicacion: false, oficio: false, proveedor: false });
  const sinUbicacion = Revision.formularioDe(valores({ ubicacion: null }), catalogo());
  assert.equal(sinUbicacion.fueraDeLista.ubicacion, false, "sin ubicación no hay nada fuera de lista");
  const ambigua = Revision.formularioDe(valoresAmbiguos({ proveedor_codigo: "P-01", proveedor_nombre: "Proveedor Ejemplo Uno" }), catalogo());
  assert.equal(ambigua.fueraDeLista.proveedor, false, "con el oficio ambiguo, el vigente vale (F-056 R15)");
  assert.equal(ambigua.fueraDeLista.oficio, false);
});

// --- R10 · el cuerpo de una acción -----------------------------------------------------------

test("f038 R10: aprobar y recuperar llevan exactamente las seis claves comunes", () => {
  const fila = incidencia({ revision_id: 7 });
  for (const accion of ["aprobar", "recuperar"]) {
    assert.deepEqual(Revision.cuerpoDeAccion(fila, accion, {}, IDENTIDAD), {
      incidencia_id: ID_1,
      accion: accion,
      usuario_oid: OID,
      usuario_correo: CORREO,
      confirmado: true,
      revision_previa: 7,
    });
  }
});

test("f038 R10: sin revisiones, revision_previa es null", () => {
  assert.equal(Revision.cuerpoDeAccion(incidencia(), "aprobar", {}, IDENTIDAD).revision_previa, null);
});

test("f038 R10: editar lleva además `valores` con sus ocho claves, y nada más", () => {
  const formulario = Revision.formularioDe(valores(), catalogo());
  formulario.ubicacion = "Baño ejemplo";
  const valoresPedidos = Object.assign(Revision.valoresDelFormulario(formulario), { clave_de_mas: "x" });
  const cuerpo = Revision.cuerpoDeAccion(incidencia({ revision_id: 2 }), "editar", { valores: valoresPedidos, motivo: "no va" }, IDENTIDAD);
  assert.deepEqual(Object.keys(cuerpo).sort(), [
    "accion",
    "confirmado",
    "incidencia_id",
    "revision_previa",
    "usuario_correo",
    "usuario_oid",
    "valores",
  ]);
  assert.deepEqual(Object.keys(cuerpo.valores).sort(), [
    "descripcion",
    "detalle",
    "listado",
    "oficio_codigo",
    "proveedor_codigo",
    "ubicacion",
    "unidad_codigo",
    "urgencia",
  ]);
  assert.equal(cuerpo.valores.ubicacion, "Baño ejemplo");
  assert.equal(cuerpo.confirmado, true);
});

test("f038 R10: descartar lleva el motivo recortado si lo hay, y sin motivo no lleva la clave", () => {
  const conMotivo = Revision.cuerpoDeAccion(incidencia(), "descartar", { motivo: "  Repetida, de ejemplo  " }, IDENTIDAD);
  assert.equal(conMotivo.motivo, "Repetida, de ejemplo");
  assert.equal(Object.keys(conMotivo).length, 7);
  const sinMotivo = Revision.cuerpoDeAccion(incidencia(), "descartar", { motivo: "   " }, IDENTIDAD);
  assert.equal("motivo" in sinMotivo, false);
  assert.equal(Object.keys(sinMotivo).length, 6);
  assert.equal("motivo" in Revision.cuerpoDeAccion(incidencia(), "descartar", {}, IDENTIDAD), false);
});

test("f038 R10/R11: un motivo de más de 500 no sale", () => {
  assert.throws(() => Revision.cuerpoDeAccion(incidencia(), "descartar", { motivo: "x".repeat(501) }, IDENTIDAD));
  assert.equal(Revision.cuerpoDeAccion(incidencia(), "descartar", { motivo: "x".repeat(500) }, IDENTIDAD).motivo.length, 500);
});

test("f038 R10: sin oid, sin correo, con una acción desconocida o editar sin valores, no hay cuerpo", () => {
  // Que la función exista: si no, cualquier `throws` pasaría por un TypeError.
  assert.equal(typeof Revision.cuerpoDeAccion, "function");
  assert.throws(() => Revision.cuerpoDeAccion(incidencia(), "aprobar", {}, { usuarioOid: "", correo: CORREO }));
  assert.throws(() => Revision.cuerpoDeAccion(incidencia(), "aprobar", {}, { usuarioOid: OID, correo: "" }));
  assert.throws(() => Revision.cuerpoDeAccion(incidencia(), "aprobar", {}, null));
  assert.throws(() => Revision.cuerpoDeAccion(incidencia(), "borrar", {}, IDENTIDAD));
  assert.throws(() => Revision.cuerpoDeAccion(incidencia(), "editar", {}, IDENTIDAD));
});

/**
 * C-B1-1 (review del Bloque 1) · los sitios donde la fuente escribe la clave
 * `confirmado`: como propiedad de un literal (`confirmado:`, `"confirmado":`),
 * como asignación (`x.confirmado =`) o por corchetes (`x["confirmado"]`).
 * Devuelve el índice de cada uno. Los comentarios no cuentan.
 */
function sitiosDeConfirmado(fuente) {
  const sinComentarios = fuente
    .replace(/\/\*[\s\S]*?\*\//g, (bloque) => bloque.replace(/[^\n]/g, " "))
    .replace(/\/\/[^\n]*/g, (linea) => " ".repeat(linea.length));
  const patron = /["']?\bconfirmado\b["']?\s*[:=](?!=)|\[\s*["']confirmado["']\s*\]/g;
  const sitios = [];
  let encontrado;
  while ((encontrado = patron.exec(sinComentarios)) !== null) {
    sitios.push(encontrado.index);
  }
  return sitios;
}

/** `[inicio, fin)` del cuerpo de `function nombre`: hasta la siguiente `function` del módulo. */
function tramoDeLaFuncion(fuente, nombre) {
  const inicio = fuente.indexOf("function " + nombre + "(");
  assert.notEqual(inicio, -1, `no está function ${nombre}`);
  const siguiente = fuente.indexOf("\n  function ", inicio + 1);
  return [inicio, siguiente === -1 ? fuente.length : siguiente];
}

/** La guardia: un solo sitio, y dentro de `cuerpoDeAccion`. Lanza si no. */
function exigirUnSoloSitioDeConfirmado(fuente) {
  const sitios = sitiosDeConfirmado(fuente);
  assert.equal(sitios.length, 1, `la confirmación se escribe en ${sitios.length} sitios; tiene que ser uno`);
  const [inicio, fin] = tramoDeLaFuncion(fuente, "cuerpoDeAccion");
  assert.ok(sitios[0] > inicio && sitios[0] < fin, "la confirmación se escribe fuera de cuerpoDeAccion");
}

test("f038 R10: confirmado: true se escribe en UN solo sitio de js/revision.js, dentro de cuerpoDeAccion", () => {
  const fuente = fs.readFileSync(path.join(__dirname, "..", "js", "revision.js"), "utf-8");

  exigirUnSoloSitioDeConfirmado(fuente);

  // Control no ciego, en memoria (nunca en el árbol): cada forma de escribir un
  // segundo sitio hace saltar la guardia, y uno solo pero fuera de su función
  // también.
  const ancla = "const cuerpo = cuerpoDeAccion(antes, accion, extra, this.usuario);";
  assert.ok(fuente.includes(ancla), "el ancla del control no está en la fuente");
  for (const segundo of [
    'cuerpo["confirmado"] = true;',
    "cuerpo.confirmado = true;",
    'const otro = { "confirmado": true };',
    "const otro = { confirmado: true };",
  ]) {
    const estropeada = fuente.replace(ancla, ancla + "\n        " + segundo);
    assert.throws(() => exigirUnSoloSitioDeConfirmado(estropeada), /2 sitios/, segundo);
  }
  const movida = fuente
    .replace(/ {6}confirmado: true,\r?\n/, "")
    .replace(ancla, ancla + "\n        cuerpo.confirmado = true;");
  assert.equal(sitiosDeConfirmado(movida).length, 1, "el control de «fuera» no ha movido el sitio");
  assert.throws(() => exigirUnSoloSitioDeConfirmado(movida), /fuera de cuerpoDeAccion/);
  // Un comentario que lo nombra no es un sitio.
  assert.equal(sitiosDeConfirmado(fuente + "\n// confirmado: true\n/* x.confirmado = true */").length, 1);
});

test("f038 R10: puedeActuar: sin oid, sin correo o guardando, no", () => {
  assert.equal(Revision.puedeActuar(IDENTIDAD, false), true);
  assert.equal(Revision.puedeActuar({ usuarioOid: "", correo: CORREO }, false), false);
  assert.equal(Revision.puedeActuar({ usuarioOid: OID, correo: "" }, false), false);
  assert.equal(Revision.puedeActuar(null, false), false);
  assert.equal(Revision.puedeActuar(IDENTIDAD, true), false);
});

// --- R12 · qué hacer con cada error (la tabla entera) -------------------------------------------

test("f038 R12: 400 peticion_invalida es un fallo de la página: no se ha guardado nada", () => {
  const que = Revision.queHacerConElError(errorApi(400, "peticion_invalida"), true);
  assert.equal(que.mensaje, "La página ha mandado algo que el servicio no acepta; no se ha guardado nada. Recarga la página.");
  assert.equal(que.recargar, false);
});

test("f038 R12: 400 valores_no_validos da el problema junto a cada campo; el formulario sigue", () => {
  const que = Revision.queHacerConElError(
    errorApi(400, "valores_no_validos", {
      error: "2 campo(s) de 'valores' no valen contra Sigrid hoy",
      codigo: "valores_no_validos",
      errores: [
        { campo: "ubicacion", problema: "no es una de las ubicaciones de la tipología de esa unidad en Sigrid" },
        { campo: "proveedor_codigo", problema: "ese proveedor no está en la obra con ese oficio en Sigrid" },
      ],
    }),
    true,
  );
  assert.deepEqual(que.erroresPorCampo, {
    ubicacion: "no es una de las ubicaciones de la tipología de esa unidad en Sigrid",
    proveedor_codigo: "ese proveedor no está en la obra con ese oficio en Sigrid",
  });
  assert.equal(que.recargar, false);
  assert.ok(que.mensaje);
});

test("f038 R12: 400 sin_cambios: «No hay cambios que guardar»; el formulario sigue", () => {
  const que = Revision.queHacerConElError(errorApi(400, "sin_cambios"), true);
  assert.match(que.mensaje, /No hay cambios que guardar/);
  assert.equal(que.recargar, false);
  assert.equal(que.erroresPorCampo, null);
});

test("f038 R12: 404 incidencia_no_encontrada: ya no está, y primera página", () => {
  const que = Revision.queHacerConElError(errorApi(404, "incidencia_no_encontrada"), true);
  assert.match(que.mensaje, /Esta incidencia ya no está en la bandeja/);
  assert.equal(que.recargar, true);
});

test("f038 R12: 404 obra_sin_unidades, 409 obra_ambigua y catalogo_sin_verificar: el texto del servicio", () => {
  for (const [http, codigo] of [[404, "obra_sin_unidades"], [409, "obra_ambigua"], [409, "catalogo_sin_verificar"]]) {
    const que = Revision.queHacerConElError(errorApi(http, codigo, null, `texto de ${codigo}, inventado`), true);
    assert.equal(que.mensaje, `texto de ${codigo}, inventado`);
    assert.equal(que.recargar, false);
  }
});

test("f038 R12: 409 accion_no_permitida dice el estado en que está, y primera página", () => {
  const que = Revision.queHacerConElError(
    errorApi(409, "accion_no_permitida", { error: "x", codigo: "accion_no_permitida", estado: "volcada", acciones: [] }),
    true,
  );
  assert.equal(que.mensaje, "Esta incidencia está volcada a Sigrid: ya no admite esa acción.");
  assert.equal(que.recargar, true);
  const aprobada = Revision.queHacerConElError(
    errorApi(409, "accion_no_permitida", { estado: "aprobada", acciones: ["editar", "descartar"] }),
    true,
  );
  assert.equal(aprobada.mensaje, "Esta incidencia está aprobada: ya no admite esa acción.");
});

test("f038 R12: 409 revision_desactualizada: «otra persona la ha cambiado», y primera página", () => {
  const que = Revision.queHacerConElError(errorApi(409, "revision_desactualizada"), true);
  assert.match(que.mensaje, /Otra persona la ha cambiado/);
  assert.equal(que.recargar, true);
});

test("f038 R12: 409 incidencia_no_aprobable: sus motivos en texto", () => {
  const que = Revision.queHacerConElError(
    errorApi(409, "incidencia_no_aprobable", { motivos: ["sin_ubicacion", "oficio_ambiguo", "motivo_raro"] }),
    true,
  );
  assert.deepEqual(que.motivos, ["Falta la ubicación", "Elige el código del oficio: hay varios en la obra", "motivo_raro"]);
  assert.match(que.mensaje, /Falta la ubicación/);
  assert.equal(que.recargar, false);
});

test("f038 R12: 409 bandeja_demasiado_grande: la obra pasa del tope, con su total", () => {
  const que = Revision.queHacerConElError(errorApi(409, "bandeja_demasiado_grande", { total: 12345 }), false);
  assert.match(que.mensaje, /12345/);
  assert.match(que.mensaje, /tope/);
  assert.match(que.mensaje, /no se puede revisar aquí/);
  assert.equal(que.recargar, false);
});

test("f038 R12: 500 sin codigo: el texto del servicio y, en una acción, que no se ha guardado nada", () => {
  const enAccion = Revision.queHacerConElError(errorApi(500, null, null, "configuración rota, inventado"), true);
  assert.match(enAccion.mensaje, /^configuración rota, inventado/);
  assert.match(enAccion.mensaje, /no se ha guardado nada/i);
  const enLectura = Revision.queHacerConElError(errorApi(500, null, null, "configuración rota, inventado"), false);
  assert.equal(enLectura.mensaje, "configuración rota, inventado");
});

test("f038 R12/R26: 503 sin codigo: el texto del servicio, que dice que no se ha escrito nada", () => {
  const que = Revision.queHacerConElError(errorApi(503, null, null, "no se ha podido hablar con Sigrid: no se ha escrito nada"), true);
  assert.equal(que.mensaje, "no se ha podido hablar con Sigrid: no se ha escrito nada");
  assert.equal(que.recargar, false);
});

test("f038 R12: una acción sin respuesta: «no se sabe si se ha guardado» y primera página", () => {
  const que = Revision.queHacerConElError(errorApi(null), true);
  assert.equal(que.mensaje, "No se sabe si se ha guardado: recarga para verlo.");
  assert.equal(que.recargar, true);
});

test("f038 R12: una lectura sin respuesta no dice «no se sabe si se ha guardado»", () => {
  const que = Revision.queHacerConElError(errorApi(null, null, null, "No se pudo contactar con el servicio."), false);
  assert.doesNotMatch(que.mensaje, /guardado/);
  assert.equal(que.recargar, false);
});

test("f038 R12: un codigo que no está en la tabla se trata por su HTTP, con el texto del servicio", () => {
  const que = Revision.queHacerConElError(errorApi(409, "codigo_nuevo", null, "texto nuevo, inventado"), true);
  assert.equal(que.mensaje, "texto nuevo, inventado");
  assert.equal(que.recargar, false);
  assert.equal(Revision.queHacerConElError(null, true).mensaje, "Error desconocido.");
});

// --- R13 · la guarda de salida ---------------------------------------------------------------

test("f038 R13: hayEdicionSinGuardar con y sin cambios, y con un estado ilegible", () => {
  const vigentes = valores();
  const formulario = Revision.formularioDe(vigentes, catalogo());
  assert.equal(Revision.hayEdicionSinGuardar({ formulario: formulario }), false, "abierto sin tocar: no pregunta");
  formulario.descripcion = "Otra descripcion de ejemplo";
  assert.equal(Revision.hayEdicionSinGuardar({ formulario: formulario }), true);
  assert.equal(Revision.hayEdicionSinGuardar({ formulario: null }), false);
  assert.equal(Revision.hayEdicionSinGuardar(null), false);
  assert.equal(Revision.hayEdicionSinGuardar(undefined), false);
  assert.equal(Revision.hayEdicionSinGuardar({ formulario: { roto: true } }), false, "ilegible: no pregunta");
});

// --- R3 · la obra de la URL --------------------------------------------------------------------

test("f038 R3: obraDeLaUrl lee ?obra= de la cadena de consulta", () => {
  assert.equal(Revision.obraDeLaUrl("?obra=9901"), "9901");
  assert.equal(Revision.obraDeLaUrl("?x=1&obra=%209901%20"), "9901");
  assert.equal(Revision.obraDeLaUrl(""), "");
  assert.equal(Revision.obraDeLaUrl(undefined), "");
});

// --- El componente (con un api doble) -----------------------------------------------------------

function apiDoble(guion) {
  const llamadas = [];
  const api = {};
  for (const nombre of ["identidad", "revision", "historialRevision", "accionRevision"]) {
    api[nombre] = async (...args) => {
      llamadas.push({ nombre, args });
      const paso = guion[nombre];
      const valor = Array.isArray(paso) ? paso.shift() : paso;
      if (typeof valor === "function") {
        return valor(...args);
      }
      if (valor instanceof Error) {
        throw valor;
      }
      return valor;
    };
  }
  return { api, llamadas };
}

function componente(guion, extra) {
  const { api, llamadas } = apiDoble(
    Object.assign(
      {
        identidad: IDENTIDAD,
        revision: () => respuesta(),
        historialRevision: { incidencia_id: ID_1, importada: null, revisiones: [] },
      },
      guion || {},
    ),
  );
  const app = Revision.crearAppRevision(Object.assign({ api: api, parametros: "" }, extra || {}));
  return { app, llamadas };
}

function nombres(llamadas) {
  return llamadas.map((l) => l.nombre);
}

test("f038 R3: el componente arranca pidiendo quién es; sin ?obra= no carga nada", async () => {
  const { app, llamadas } = componente();
  await app.iniciar();
  assert.deepEqual(nombres(llamadas), ["identidad"]);
  assert.deepEqual(app.usuario, IDENTIDAD);
  assert.equal(app.obra, "");
});

test("f038 R3: con ?obra= el campo sale relleno y se pide la primera página (solo lee)", async () => {
  const { app, llamadas } = componente({}, { parametros: "?obra=9901" });
  await app.iniciar();
  assert.equal(app.obra, "9901");
  assert.deepEqual(nombres(llamadas), ["identidad", "revision"]);
  assert.deepEqual(llamadas[1].args, ["9901", { estado: "activas", con_motivos: undefined }, undefined]);
});

test("f038 R3/R5/R7: cargar pide la primera página sin cursor y deja resumen, lista y «N de M»", async () => {
  const { app, llamadas } = componente({
    revision: () => respuesta({ total_filtrado: 5, siguiente: "cursor-inventado-1", incidencias: [incidencia({ incidencia_id: ID_1 }), incidencia({ incidencia_id: ID_2 })] }),
  });
  await app.iniciar();
  app.obra = " 9901 ";
  await app.cargar();
  assert.deepEqual(llamadas[1].args, ["9901", { estado: "activas", con_motivos: undefined }, undefined]);
  assert.equal(app.incidencias.length, 2);
  assert.equal(app.siguiente, "cursor-inventado-1");
  assert.equal(app.nDeM, "2 de 5");
  assert.deepEqual(app.resumen, resumen());
  assert.equal(app.vista().filas.length, 2);
  assert.equal(app.vistaResumen().total, 10);
  assert.equal(app.cargando, false);
});

test("f038 R7: «Cargar más» pide con el cursor y los MISMOS filtros, y añade sin repetir", async () => {
  const { app, llamadas } = componente({
    revision: [
      respuesta({ total_filtrado: 3, siguiente: "cursor-inventado-1", incidencias: [incidencia({ incidencia_id: ID_1 }), incidencia({ incidencia_id: ID_2 })] }),
      respuesta({ total_filtrado: 3, siguiente: null, resumen: resumen({ total: 11 }), incidencias: [incidencia({ incidencia_id: ID_2 }), incidencia({ incidencia_id: ID_3 })] }),
    ],
  });
  await app.iniciar();
  app.obra = "9901";
  app.filtros.estado = "editada";
  app.filtros.conMotivos = true;
  await app.cargar();
  // Lo que se escriba después en el campo o en los filtros no cambia la página siguiente.
  app.obra = "otra-escrita-despues";
  app.filtros.estado = "todas";
  await app.cargarMas();
  assert.deepEqual(llamadas[2].args, ["9901", { estado: "editada", con_motivos: true }, "cursor-inventado-1"]);
  assert.deepEqual(app.incidencias.map((i) => i.incidencia_id), [ID_1, ID_2, ID_3]);
  assert.equal(app.siguiente, null);
  assert.equal(app.nDeM, "3 de 3");
  assert.equal(app.resumen.total, 11, "el resumen es el de la última respuesta");
  await app.cargarMas();
  assert.equal(llamadas.length, 3, "sin siguiente, «Cargar más» no pide nada");
});

test("f038 R6: cambiar un filtro vuelve a pedir la primera página", async () => {
  const { app, llamadas } = componente({
    revision: [
      respuesta({ siguiente: "cursor-inventado-1", incidencias: [incidencia({ incidencia_id: ID_1 })] }),
      respuesta({ siguiente: null, incidencias: [incidencia({ incidencia_id: ID_3 })] }),
    ],
  });
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  app.filtros.conMotivos = true;
  await app.cambiarFiltro();
  assert.deepEqual(llamadas[2].args, ["9901", { estado: "activas", con_motivos: true }, undefined]);
  assert.deepEqual(app.incidencias.map((i) => i.incidencia_id), [ID_3], "la lista se vacía, no se añade");
});

test("f038 R3/R12: un error al cargar se enseña y vacía lo que había (filas, siguiente, resumen, «N de M»)", async () => {
  // C-B1-2 (review del Bloque 1): se parte de una página BUENA ya cargada. Tras
  // una acción, `actuar` recarga; si esa recarga falla, la página no puede
  // seguir enseñando filas viejas con su `revision_id` viejo.
  const { app } = componente({
    revision: [
      respuesta({ total_filtrado: 5, siguiente: "cursor-inventado-1", incidencias: [incidencia({ incidencia_id: ID_1 }), incidencia({ incidencia_id: ID_2 })] }),
      errorApi(409, "bandeja_demasiado_grande", { total: 12000 }),
    ],
  });
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  assert.equal(app.incidencias.length, 2, "la primera carga es buena");
  assert.equal(app.siguiente, "cursor-inventado-1");
  assert.notEqual(app.resumen, null);
  assert.equal(app.nDeM, "2 de 5");

  await app.cargar();

  assert.match(app.errorCarga, /12000/);
  assert.deepEqual(app.incidencias, []);
  assert.equal(app.siguiente, null);
  assert.equal(app.resumen, null);
  assert.equal(app.nDeM, "");
  assert.equal(app.cargando, false);
});

test("f038 R3: sin obra, cargar no pide nada", async () => {
  const { app, llamadas } = componente();
  await app.iniciar();
  app.obra = "   ";
  await app.cargar();
  assert.deepEqual(nombres(llamadas), ["identidad"]);
});

test("f038 R8: abrirDetalle(incidencia_id) abre la fila y pide su historial", async () => {
  const { app, llamadas } = componente({
    historialRevision: {
      incidencia_id: ID_1,
      importada: null,
      revisiones: [{ revision_id: 1, accion: "editar", revisado_at_utc: "2026-10-20T08:00:00+00:00", correo: CORREO, campos_cambiados: ["ubicacion"], motivo: null }],
    },
  });
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  await app.abrirDetalle(ID_1);
  assert.equal(app.abierta, ID_1);
  assert.deepEqual(llamadas[2], { nombre: "historialRevision", args: [ID_1] });
  assert.equal(app.historial.revisiones[0].quien, CORREO);
  assert.equal(app.detalle().find((c) => c.campo === "ubicacion").valor, "Cocina ejemplo");
});

test("f038 R8: un error del historial se enseña sin cerrar el detalle", async () => {
  const { app } = componente({ historialRevision: errorApi(503, null, null, "sin base, inventado") });
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  await app.abrirDetalle(ID_1);
  assert.equal(app.abierta, ID_1);
  assert.equal(app.errorHistorial, "sin base, inventado");
});

test("f038 R9/R11: abrirFormulario(incidencia_id) abre el formulario solo si el estado admite editar", async () => {
  const { app } = componente({
    revision: () => respuesta({
      incidencias: [
        incidencia({ incidencia_id: ID_1, estado: "nueva" }),
        incidencia({ incidencia_id: ID_2, estado: "descartada", motivos_no_aprobable: null }),
        incidencia({ incidencia_id: ID_3, estado: "volcada" }),
      ],
    }),
  });
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  await app.abrirFormulario(ID_1);
  assert.equal(app.abierta, ID_1);
  assert.equal(app.formulario.unidad_codigo, "U-01");
  app.cancelarFormulario();
  assert.equal(app.formulario, null);
  await app.abrirFormulario(ID_2);
  assert.equal(app.formulario, null, "una descartada no se edita");
  await app.abrirFormulario(ID_3);
  assert.equal(app.formulario, null, "R21.6: una volcada no tiene formulario");
});

test("f038 R10/R12: aprobar con un clic manda el cuerpo, sustituye la fila y ajusta el resumen sin recargar", async () => {
  const despues = incidencia({ estado: "aprobada", revision_id: 1, revisado_por: CORREO, revisado_at_utc: "2026-10-20T08:00:00+00:00" });
  const { app, llamadas } = componente({ accionRevision: despues });
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  await app.aprobar(ID_1);
  const acciones = llamadas.filter((l) => l.nombre === "accionRevision");
  assert.equal(acciones.length, 1);
  assert.deepEqual(acciones[0].args[0], {
    incidencia_id: ID_1,
    accion: "aprobar",
    usuario_oid: OID,
    usuario_correo: CORREO,
    confirmado: true,
    revision_previa: null,
  });
  assert.equal(app.incidencias[0].estado, "aprobada");
  assert.equal(app.resumen.por_estado.nueva, 3);
  assert.equal(app.resumen.por_estado.aprobada, 2);
  assert.equal(nombres(llamadas).filter((n) => n === "revision").length, 1, "no se recarga");
  assert.equal(app.guardando, false);
});

test("f038 R10: sin correo en la sesión, ninguna acción sale", async () => {
  const { app, llamadas } = componente({ identidad: { usuarioOid: OID, correo: "" } });
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  assert.equal(app.puedeActuar(), false);
  await app.aprobar(ID_1);
  await app.recuperar(ID_1);
  assert.equal(llamadas.filter((l) => l.nombre === "accionRevision").length, 0);
});

test("f038 R10: mientras una acción se guarda, ninguna otra sale", async () => {
  let soltar;
  const pendiente = new Promise((resolver) => {
    soltar = resolver;
  });
  const { app, llamadas } = componente({
    accionRevision: () => pendiente.then(() => incidencia({ estado: "aprobada", revision_id: 1 })),
  });
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  const primera = app.aprobar(ID_1);
  assert.equal(app.guardando, true);
  assert.equal(app.puedeActuar(), false);
  // O-B1-6 (review del Bloque 1): los intentos de mientras se lanzan SIN
  // esperarlos antes de soltar la primera; si la puerta fallara, esperarlos
  // aquí colgaría el test en vez de ponerlo en rojo.
  const segunda = app.aprobar(ID_1);
  app.pedirDescarte(ID_1);
  const tercera = app.confirmarDescarte(ID_1);
  const mientras = llamadas.filter((l) => l.nombre === "accionRevision").length;
  soltar();
  await Promise.all([primera, segunda, tercera]);
  assert.equal(mientras, 1, "mientras se guarda, ninguna otra sale");
  assert.equal(llamadas.filter((l) => l.nombre === "accionRevision").length, 1, "un doble clic no produce dos");
});

test("f038 R11: una acción que el estado no ofrece no sale", async () => {
  const { app, llamadas } = componente({
    revision: () => respuesta({ incidencias: [incidencia({ estado: "aprobada", revision_id: 1 })] }),
  });
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  await app.aprobar(ID_1);
  await app.recuperar(ID_1);
  assert.equal(llamadas.filter((l) => l.nombre === "accionRevision").length, 0);
});

test("f038 R11: descartar pide un segundo clic y lleva el motivo", async () => {
  const { app, llamadas } = componente({
    accionRevision: incidencia({ estado: "descartada", revision_id: 1, motivos_no_aprobable: null }),
  });
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  app.pedirDescarte(ID_1);
  assert.equal(app.confirmandoDescarte, ID_1);
  assert.equal(llamadas.filter((l) => l.nombre === "accionRevision").length, 0, "el primer clic no descarta");
  app.motivoDescarte = "Repetida, de ejemplo";
  await app.confirmarDescarte(ID_1);
  const acciones = llamadas.filter((l) => l.nombre === "accionRevision");
  assert.equal(acciones.length, 1);
  assert.equal(acciones[0].args[0].accion, "descartar");
  assert.equal(acciones[0].args[0].motivo, "Repetida, de ejemplo");
  assert.equal(app.confirmandoDescarte, null);
  assert.equal(app.incidencias[0].estado, "descartada");
  assert.equal(app.resumen.por_estado.descartada, 2);
});

test("f038 R11: confirmar el descarte de otra fila que la pedida no descarta nada", async () => {
  const { app, llamadas } = componente({
    revision: () => respuesta({ incidencias: [incidencia({ incidencia_id: ID_1 }), incidencia({ incidencia_id: ID_2 })] }),
  });
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  app.pedirDescarte(ID_1);
  await app.confirmarDescarte(ID_2);
  assert.equal(llamadas.filter((l) => l.nombre === "accionRevision").length, 0);
});

test("f038 R9/R10: guardar la edición manda `valores` del formulario y cierra el formulario", async () => {
  const despues = incidencia({ estado: "editada", revision_id: 1, vigentes: valores({ ubicacion: "Baño ejemplo" }), cambios: ["ubicacion"] });
  const { app, llamadas } = componente({ accionRevision: despues });
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  await app.abrirFormulario(ID_1);
  assert.equal(app.hayEdicionSinGuardar(), false);
  app.formulario.ubicacion = "Baño ejemplo";
  assert.equal(app.hayEdicionSinGuardar(), true);
  await app.guardarEdicion();
  const acciones = llamadas.filter((l) => l.nombre === "accionRevision");
  assert.equal(acciones.length, 1);
  assert.equal(acciones[0].args[0].accion, "editar");
  assert.equal(acciones[0].args[0].valores.ubicacion, "Baño ejemplo");
  assert.equal(app.formulario, null);
  assert.equal(app.incidencias[0].estado, "editada");
});

test("f038 R9 (e): guardar sin cambios no manda nada y lo dice", async () => {
  const { app, llamadas } = componente();
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  await app.abrirFormulario(ID_1);
  app.formulario.descripcion = "  Grieta de   ejemplo en el alicatado ";
  await app.guardarEdicion();
  assert.equal(llamadas.filter((l) => l.nombre === "accionRevision").length, 0);
  assert.match(app.mensajeAccion, /No hay cambios que guardar/);
  assert.notEqual(app.formulario, null, "el formulario sigue abierto");
});

test("f038 R9: el componente revalida la ubicación al cambiar la unidad y el proveedor al cambiar el oficio", async () => {
  const { app } = componente();
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  await app.abrirFormulario(ID_1);
  app.formulario.unidad_codigo = "U-03";
  app.cambiarUnidad();
  assert.equal(app.formulario.ubicacion, "");
  assert.match(app.formulario.aviso, /esta ubicación no es de la nueva unidad/i);
  app.formulario.oficio_codigo = "9004";
  app.cambiarOficio();
  assert.equal(app.formulario.proveedor_codigo, "");
});

test("f038 R12: 400 valores_no_validos deja el formulario abierto con el problema junto al campo", async () => {
  const { app, llamadas } = componente({
    accionRevision: errorApi(400, "valores_no_validos", { errores: [{ campo: "ubicacion", problema: "problema inventado" }] }),
  });
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  await app.abrirFormulario(ID_1);
  app.formulario.ubicacion = "Baño ejemplo";
  await app.guardarEdicion();
  assert.deepEqual(app.erroresPorCampo, { ubicacion: "problema inventado" });
  assert.notEqual(app.formulario, null);
  assert.equal(nombres(llamadas).filter((n) => n === "revision").length, 1, "no recarga");
});

test("f038 R12: 409 revision_desactualizada: lo dice y vuelve a pedir la primera página", async () => {
  const { app, llamadas } = componente({ accionRevision: errorApi(409, "revision_desactualizada") });
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  await app.abrirFormulario(ID_1);
  app.formulario.ubicacion = "Baño ejemplo";
  await app.guardarEdicion();
  assert.match(app.mensajeAccion, /Otra persona la ha cambiado/);
  const lecturas = llamadas.filter((l) => l.nombre === "revision");
  assert.equal(lecturas.length, 2);
  assert.equal(lecturas[1].args[2], undefined, "primera página: sin cursor");
  assert.equal(app.formulario, null);
});

test("f038 R12: una acción sin respuesta no se da por fallida: «no se sabe» y primera página", async () => {
  const { app, llamadas } = componente({ accionRevision: errorApi(null) });
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  await app.aprobar(ID_1);
  assert.equal(app.mensajeAccion, "No se sabe si se ha guardado: recarga para verlo.");
  assert.equal(llamadas.filter((l) => l.nombre === "revision").length, 2, "vuelve a pedir la primera página");
  assert.equal(llamadas.filter((l) => l.nombre === "accionRevision").length, 1, "no se reintenta sola");
  assert.equal(app.guardando, false);
});

test("f038 R12: 409 incidencia_no_aprobable enseña sus motivos y no recarga", async () => {
  const { app, llamadas } = componente({ accionRevision: errorApi(409, "incidencia_no_aprobable", { motivos: ["sin_ubicacion"] }) });
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  await app.aprobar(ID_1);
  assert.match(app.mensajeAccion, /Falta la ubicación/);
  assert.equal(llamadas.filter((l) => l.nombre === "revision").length, 1);
});

test("f038 R13: hayEdicionSinGuardar del componente sirve al beforeunload", async () => {
  const { app } = componente();
  await app.iniciar();
  assert.equal(app.hayEdicionSinGuardar(), false);
  assert.equal(Revision.hayEdicionSinGuardar(app), false);
});

test("f038 R15: js/revision.js no escribe en console ni en el almacenamiento del navegador", () => {
  const fuente = fs.readFileSync(path.join(__dirname, "..", "js", "revision.js"), "utf-8");
  assert.doesNotMatch(fuente, /console\./);
  assert.doesNotMatch(fuente, /localStorage|sessionStorage|indexedDB/);
  assert.doesNotMatch(fuente, /\/revision\/normalizar/, "R23: la página no normaliza");
});

// R21.7 · `volcado_por` es un correo (D-8): ni a la consola ni al almacenamiento.
// Se EJECUTA el recorrido del componente con una volcada, una en duda y un
// intento rechazado (cargar, pintar, abrir el detalle y su historial) con la
// consola y el almacenamiento espiados; el control repite lo mismo con un
// `js/revision.js` estropeado en memoria que sí escribe el correo.

const METODOS_DE_CONSOLA = ["log", "info", "warn", "error", "debug", "trace", "table", "dir"];

async function conConsolaYAlmacenamientoEspiados(hacer) {
  const tocados = [];
  const originales = {};
  for (const metodo of METODOS_DE_CONSOLA) {
    originales[metodo] = console[metodo];
    console[metodo] = (...args) => tocados.push(`console.${metodo}(${args.map(String).join(", ")})`);
  }
  const descriptores = {};
  for (const nombre of ["localStorage", "sessionStorage"]) {
    descriptores[nombre] = Object.getOwnPropertyDescriptor(globalThis, nombre);
    const almacen = {};
    for (const metodo of ["getItem", "setItem", "removeItem", "clear", "key"]) {
      almacen[metodo] = (...args) => tocados.push(`${nombre}.${metodo}(${args.map(String).join(", ")})`);
    }
    Object.defineProperty(globalThis, nombre, { value: almacen, configurable: true, writable: true });
  }
  try {
    await hacer();
  } finally {
    for (const metodo of METODOS_DE_CONSOLA) console[metodo] = originales[metodo];
    for (const nombre of ["localStorage", "sessionStorage"]) {
      if (descriptores[nombre]) Object.defineProperty(globalThis, nombre, descriptores[nombre]);
      else delete globalThis[nombre];
    }
  }
  return tocados;
}

/** Lo que el recorrido de una página con volcados deja en la consola o en el almacenamiento. Vacío = correcto. */
async function rastroDelVolcado(Modulo) {
  return conConsolaYAlmacenamientoEspiados(async () => {
    const incidencias = [
      incidencia({ incidencia_id: ID_1, estado: "volcada", volcado: objetoVolcado({ volcado_por: OTRO_CORREO }) }),
      incidencia({ incidencia_id: ID_2, estado: "en_duda", volcado: objetoVolcado({ estado: "en_duda", sigrid_cod: null, volcado_por: OTRO_CORREO }) }),
      incidencia({
        incidencia_id: ID_3,
        estado: "aprobada",
        volcado: objetoVolcado({ estado: "rechazado", sigrid_cod: null, volcado_por: OTRO_CORREO, motivo: "error_de_escritura" }),
      }),
    ];
    const { api } = apiDoble({
      identidad: IDENTIDAD,
      revision: () => respuesta({ incidencias: incidencias }),
      historialRevision: { incidencia_id: ID_1, importada: null, revisiones: [] },
    });
    const app = Modulo.crearAppRevision({ api: api, parametros: "?obra=9901" });
    await app.iniciar();
    const filas = app.vista().filas;
    assert.equal(filas.filter((f) => f.lineaVolcado && f.lineaVolcado.includes(OTRO_CORREO)).length, 3, "las tres líneas, pintadas");
    app.vistaResumen();
    for (const id of [ID_1, ID_2, ID_3]) {
      await app.abrirDetalle(id);
      app.detalle();
    }
  });
}

test("f038 R21.7: pintar volcadas y abrir su detalle no escribe nada en la consola ni en el almacenamiento", async () => {
  assert.deepEqual(await rastroDelVolcado(Revision), []);
});

for (const [nombre, estropear] of [
  ["el correo de quien volcó a console.log", (y) => `(console.log(${y}), quienLegible(${y}))`],
  ["el correo de quien volcó a localStorage", (y) => `(localStorage.setItem("quien", ${y}), quienLegible(${y}))`],
]) {
  test(`f038 R21.7: control: ${nombre} salta`, async () => {
    const fuente = fs.readFileSync(path.join(__dirname, "..", "js", "revision.js"), "utf-8");
    const ancla = "quienLegible(volcado.volcado_por)";
    assert.equal(fuente.split(ancla).length, 2, `el control no encuentra una sola vez: ${ancla}`);
    const modulo = { exports: {} };
    // eslint-disable-next-line no-new-func
    Function("module", fuente.replace(ancla, estropear("volcado.volcado_por")))(modulo);
    const rastro = await rastroDelVolcado(modulo.exports);
    assert.ok(rastro.some((r) => r.includes(OTRO_CORREO)), `${nombre}: el espía no lo ve (${rastro.join("; ")})`);
  });
}

// --- Bloque 1 bis (T1 bis) · `bandeja.html`, evaluada contra el componente ----------------------
//
// El HTML de la página se lee como texto y sus expresiones de Alpine se evalúan
// contra el componente DE VERDAD (`crearAppRevision` con el `api` doble), sin
// navegador: así se prueba lo que el texto no dice (que cada nombre existe, que
// la puerta de cada botón de acción es la de `accionesDe`, que «Aprobar» lee a
// la vez la fila y `puedeActuar()`, y el `beforeunload` de R13). La estructura
// (barra, tira, migas, pie, cargas…) la fija `tests/test_f038_front.py`.

const BANDEJA_HTML = path.join(__dirname, "..", "bandeja.html");

function leerBandeja() {
  return fs.readFileSync(BANDEJA_HTML, "utf-8");
}

const VACIOS_HTML = new Set(["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"]);
const ETIQUETA_HTML = /<(\/?)([a-zA-Z][\w-]*)((?:\s+[^\s"'=<>\/]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'>]+))?)*)\s*(\/?)>/g;
const ATRIBUTO_HTML = /([^\s"'=<>\/]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+)))?/g;

function atributosHtml(trozo) {
  const atributos = {};
  for (const m of trozo.matchAll(ATRIBUTO_HTML)) {
    atributos[m[1]] = m[2] ?? m[3] ?? m[4] ?? "";
  }
  return atributos;
}

/** `with (alcance) { return (expresión) }`: como evalúa Alpine, con `this` = el alcance en las llamadas. */
function evaluarEn(alcance, expresion) {
  // eslint-disable-next-line no-new-func
  return Function("alcance", `with (alcance) { return (${expresion}); }`)(alcance);
}

const DIRECTIVAS_DE_VALOR = /^(?:x-text|x-show|x-if|x-model|x-html|:[\w.-]+|x-bind:[\w.-]+)$/;
const DIRECTIVAS_DE_EVENTO = /^(?:@[\w.-]+|x-on:[\w.-]+|x-init)$/;
const BUCLE = /^\s*(?:\(\s*(\w+)\s*(?:,\s*(\w+)\s*)?\)|(\w+))\s+in\s+([\s\S]+)$/;

/**
 * Recorre `bandeja.html` como lo pintaría Alpine con el `alcance` dado: un
 * `x-if` falso no pinta lo de dentro; un `x-for` pinta su primer elemento (con
 * sus variables); un `x-show` falso deja el elemento oculto. Devuelve los
 * elementos con su alcance, si se ven y los problemas de evaluación (una
 * expresión que lanza, o un manejador que no es una función).
 */
function recorrerBandeja(html, alcanceBase) {
  const limpio = html.replace(/<!--[\s\S]*?-->/g, "").replace(/<script\b[^>]*>[\s\S]*?<\/script>/g, "");
  const pila = [{ nombre: "#raiz", alcance: alcanceBase, pinta: true, visible: true }];
  const elementos = [];
  const problemas = [];
  for (const m of limpio.matchAll(ETIQUETA_HTML)) {
    const [, cierre, nombreCrudo, resto, autocierre] = m;
    const nombre = nombreCrudo.toLowerCase();
    if (cierre) {
      const i = pila.map((e) => e.nombre).lastIndexOf(nombre);
      if (i > 0) pila.length = i;
      continue;
    }
    const padre = pila[pila.length - 1];
    const atributos = atributosHtml(resto);
    let alcance = padre.alcance;
    let pinta = padre.pinta;
    let visible = padre.visible;
    const evaluar = (nombreAtributo, expresion) => {
      try {
        return { valor: evaluarEn(alcance, expresion) };
      } catch (error) {
        problemas.push(`<${nombre} ${nombreAtributo}="${expresion}">: ${error.message}`);
        return { error };
      }
    };
    if (pinta && "x-for" in atributos) {
      const bucle = atributos["x-for"].match(BUCLE);
      if (!bucle) {
        problemas.push(`x-for ilegible: ${atributos["x-for"]}`);
        pinta = false;
      } else {
        const lista = evaluar("x-for", bucle[4]);
        const elementosDeLaLista = Array.isArray(lista.valor) ? lista.valor : [];
        if (!elementosDeLaLista.length) {
          pinta = false;
        } else {
          alcance = Object.create(alcance);
          alcance[bucle[1] || bucle[3]] = elementosDeLaLista[0];
          if (bucle[2]) alcance[bucle[2]] = 0;
        }
      }
    }
    if (pinta && "x-if" in atributos) {
      const condicion = evaluar("x-if", atributos["x-if"]);
      if (!condicion.valor) pinta = false;
    }
    if (pinta && "x-show" in atributos) {
      const condicion = evaluar("x-show", atributos["x-show"]);
      if (!condicion.valor) visible = false;
    }
    if (pinta) {
      for (const [nombreAtributo, expresion] of Object.entries(atributos)) {
        if (["x-for", "x-if", "x-show", "x-data"].includes(nombreAtributo)) continue;
        if (DIRECTIVAS_DE_VALOR.test(nombreAtributo)) {
          evaluar(nombreAtributo, expresion);
        } else if (DIRECTIVAS_DE_EVENTO.test(nombreAtributo)) {
          const llamada = expresion.match(/^\s*([\w$.]+)\s*\(/);
          if (llamada) {
            const funcion = evaluar(nombreAtributo, llamada[1]);
            if (!funcion.error && typeof funcion.valor !== "function") {
              problemas.push(`<${nombre} ${nombreAtributo}="${expresion}">: ${llamada[1]} no es una función del componente`);
            }
          }
        }
      }
      elementos.push({ nombre, atributos, alcance, visible });
    }
    if (!VACIOS_HTML.has(nombre) && !autocierre) {
      pila.push({ nombre, alcance, pinta, visible });
    }
  }
  return { elementos, problemas };
}

/** Lo que llama el `@click` de un botón de acción → la acción de `accionesDe` que pide. */
const ACCION_DEL_CLIC = {
  abrirFormulario: "editar",
  guardarEdicion: "editar",
  aprobar: "aprobar",
  pedirDescarte: "descartar",
  confirmarDescarte: "descartar",
  recuperar: "recuperar",
};

function accionDelBoton(elemento) {
  const llamada = (elemento.atributos["@click"] || "").match(/^\s*(\w+)\s*\(/);
  return llamada && Object.prototype.hasOwnProperty.call(ACCION_DEL_CLIC, llamada[1]) ? ACCION_DEL_CLIC[llamada[1]] : null;
}

/** Las llamadas al `api` doble de cada alcance de `alcanceConTodoAbierto` (C-B1b-2). */
const LLAMADAS_DEL_ALCANCE = new WeakMap();

/**
 * El componente con todo abierto sobre UNA incidencia en `estado`: cargada,
 * con su detalle, su historial, el formulario y el segundo clic de descartar
 * pedidos. El formulario y el descarte se fuerzan en el alcance (el componente
 * no los abre en un estado que no los admite): así lo que se mide es la puerta
 * del HTML, no la del componente.
 */
async function alcanceConTodoAbierto(estado, cambios, guion) {
  const fila = incidencia(
    Object.assign(
      {
        estado: estado,
        revision_id: "00000000-0000-4000-8000-0000000000b1",
        revisado_at_utc: "2026-10-20T08:30:00.000000+00:00",
        revisado_por: CORREO,
        cambios: ["ubicacion"],
        importados: valores({ ubicacion: null }),
      },
      cambios || {},
    ),
  );
  const { app, llamadas } = componente(Object.assign({
    revision: () => respuesta({ incidencias: [fila], siguiente: "cursor-inventado", total_filtrado: 7 }),
    historialRevision: {
      incidencia_id: ID_1,
      importada: { origen: "excel", importacion_id: "00000000-0000-4000-8000-0000000000aa", creada_at_utc: "2026-10-20T08:00:00.000000+00:00" },
      revisiones: [
        {
          revision_id: "00000000-0000-4000-8000-0000000000b1",
          accion: "editar",
          revisado_at_utc: "2026-10-20T08:30:00.000000+00:00",
          correo: CORREO,
          campos_cambiados: ["ubicacion"],
          motivo: null,
        },
      ],
    },
  }, guion || {}));
  await app.iniciar();
  app.obra = "9901";
  await app.cargar();
  await app.abrirDetalle(ID_1);
  const alcance = Object.create(app);
  alcance.formulario = Revision.formularioDe(fila.vigentes, app.catalogo);
  alcance.confirmandoDescarte = ID_1;
  alcance.motivoDescarte = "";
  alcance.erroresPorCampo = { ubicacion: "problema inventado" };
  alcance.mensajeAccion = "mensaje inventado";
  LLAMADAS_DEL_ALCANCE.set(alcance, llamadas);
  return alcance;
}

test("f038 T1 bis: cada expresión de Alpine de bandeja.html se evalúa contra el componente sin error", async () => {
  const { elementos, problemas } = recorrerBandeja(leerBandeja(), await alcanceConTodoAbierto("nueva"));
  assert.deepEqual(problemas, []);
  assert.ok(elementos.length > 50, `la página pinta ${elementos.length} elementos con todo abierto: ¿se ha leído?`);
});

test("f038 T1 bis: control: un nombre que el componente no tiene, en bandeja.html, salta", async () => {
  const html = leerBandeja();
  const alcance = await alcanceConTodoAbierto("nueva");
  for (const [viejo, nuevo] of [
    ['@click="aprobar(fila.incidencia_id)"', '@click="aprobarla(fila.incidencia_id)"'],
    ['x-text="nDeM"', 'x-text="nDeMm"'],
  ]) {
    assert.ok(html.includes(viejo), `el control no encuentra ${viejo}`);
    const { problemas } = recorrerBandeja(html.replace(viejo, nuevo), alcance);
    assert.notDeepEqual(problemas, [], `${nuevo}: el recorrido no lo ve`);
  }
});

test("f038 R11, R21.6: en cada estado, bandeja.html pinta justo los botones de accionesDe, ni uno más", async () => {
  const vistas = {};
  for (const estado of Revision.ESTADOS) {
    const { elementos, problemas } = recorrerBandeja(leerBandeja(), await alcanceConTodoAbierto(estado));
    assert.deepEqual(problemas, [], estado);
    const pintadas = new Set(
      elementos.filter((e) => e.nombre === "button" && e.visible && accionDelBoton(e)).map(accionDelBoton),
    );
    assert.deepEqual([...pintadas].sort(), Revision.accionesDe(estado).slice().sort(), `${estado}: los botones de acción pintados`);
    vistas[estado] = pintadas;
  }
  // R21.6: en una volcada o una en duda, ni un botón de acción ni el formulario.
  for (const estado of ["volcada", "en_duda"]) {
    const { elementos } = recorrerBandeja(leerBandeja(), await alcanceConTodoAbierto(estado));
    const campos = elementos.filter(
      (e) =>
        ["select", "textarea", "input"].includes(e.nombre) &&
        e.visible &&
        !/^(?:obra|filtros\.)/.test(e.atributos["x-model"] || ""),
    );
    assert.deepEqual(campos.map((e) => e.nombre), [], `${estado}: sin formulario ni motivo de descarte`);
    assert.equal(vistas[estado].size, 0, estado);
  }
});

test("f038 R11, R21.6: control: un botón fuera de su puerta, en bandeja.html, salta", async () => {
  const html = leerBandeja();
  const alcance = await alcanceConTodoAbierto("volcada");
  const sinPuerta = html.replace(/<template x-if="fila\.acciones\.includes\('aprobar'\)">/, '<template x-if="true">');
  assert.notEqual(sinPuerta, html, "el control no encuentra la puerta de «Aprobar»");
  const { elementos } = recorrerBandeja(sinPuerta, alcance);
  const pintadas = elementos.filter((e) => e.nombre === "button" && e.visible && accionDelBoton(e)).map(accionDelBoton);
  assert.deepEqual(pintadas, ["aprobar"], "una volcada con «Aprobar» tiene que verse");
});

function botonDe(elementos, metodo) {
  const botones = elementos.filter(
    (e) => e.nombre === "button" && new RegExp(`^\\s*${metodo}\\(`).test(e.atributos["@click"] || ""),
  );
  assert.equal(botones.length, 1, `un solo botón con @click="${metodo}(…)" (hay ${botones.length})`);
  return botones[0];
}

test("f038 R10, R11 (O-B1-1 a): el :disabled de «Aprobar» lee fila.aprobable Y puedeActuar(), ni uno sin el otro", async () => {
  const { elementos } = recorrerBandeja(leerBandeja(), await alcanceConTodoAbierto("nueva"));
  const aprobar = botonDe(elementos, "aprobar");
  assert.ok(":disabled" in aprobar.atributos, "«Aprobar» lleva :disabled");
  for (const aprobable of [true, false]) {
    for (const actua of [true, false]) {
      const alcance = Object.create(aprobar.alcance);
      alcance.fila = Object.assign({}, aprobar.alcance.fila, { aprobable });
      alcance.puedeActuar = () => actua;
      assert.equal(
        Boolean(evaluarEn(alcance, aprobar.atributos[":disabled"])),
        !aprobable || !actua,
        `aprobable=${aprobable}, puedeActuar()=${actua}`,
      );
    }
  }
});

test("f038 R10: sin puedeActuar() (sin oid, sin correo o guardando), ningún botón de acción está habilitado", async () => {
  const { elementos } = recorrerBandeja(leerBandeja(), await alcanceConTodoAbierto("nueva"));
  const deAccion = elementos.filter((e) => e.nombre === "button" && accionDelBoton(e));
  assert.deepEqual(
    [...new Set(deAccion.map(accionDelBoton))].sort(),
    ["aprobar", "descartar", "editar"],
    "en una nueva, los botones de editar, descartar y aprobar",
  );
  for (const boton of deAccion) {
    const alcance = Object.create(boton.alcance);
    alcance.puedeActuar = () => false;
    assert.ok(":disabled" in boton.atributos, `«${boton.atributos["@click"]}» lleva :disabled`);
    assert.equal(Boolean(evaluarEn(alcance, boton.atributos[":disabled"])), true, boton.atributos["@click"]);
  }
  const { elementos: deUnaDescartada } = recorrerBandeja(leerBandeja(), await alcanceConTodoAbierto("descartada"));
  const recuperar = botonDe(deUnaDescartada, "recuperar");
  const sinSesion = Object.create(recuperar.alcance);
  sinSesion.puedeActuar = () => false;
  assert.equal(Boolean(evaluarEn(sinSesion, recuperar.atributos[":disabled"])), true, "recuperar");
});

test("f038 R10: control: el :disabled de «Aprobar» sin puedeActuar() salta", async () => {
  const html = leerBandeja();
  const m = html.match(/@click="aprobar\(fila\.incidencia_id\)" :disabled="([^"]*)"/);
  assert.ok(m, "el control no encuentra «Aprobar» con su :disabled justo detrás del @click");
  const estropeado = html.replace(m[0], '@click="aprobar(fila.incidencia_id)" :disabled="!fila.aprobable"');
  const { elementos } = recorrerBandeja(estropeado, await alcanceConTodoAbierto("nueva"));
  const aprobar = botonDe(elementos, "aprobar");
  const alcance = Object.create(aprobar.alcance);
  alcance.puedeActuar = () => false;
  assert.equal(Boolean(evaluarEn(alcance, aprobar.atributos[":disabled"])), false, "sin puedeActuar(), el estropeado se habilita");
});

// R13 · el `beforeunload` de la página: el único <script> sin `src` de bandeja.html.

function guardaDeSalida() {
  const enLinea = [...leerBandeja().matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  assert.equal(enLinea.length, 1, "bandeja.html lleva un único <script> en línea: la guarda de salida");
  return enLinea[0];
}

/** Ejecuta la guarda en un contexto aparte; devuelve sus escuchas y cómo dispararla. */
function montarGuarda({ alpine, raiz } = {}) {
  const escuchas = [];
  const ventana = {
    addEventListener(tipo, funcion) {
      escuchas.push({ tipo, funcion });
    },
    Revision: Revision,
  };
  if (alpine !== undefined) ventana.Alpine = alpine;
  const documento = { querySelector: () => (raiz === undefined ? { esLaRaiz: true } : raiz) };
  require("node:vm").runInNewContext(guardaDeSalida(), { window: ventana, document: documento });
  return {
    escuchas,
    salir() {
      const evento = {
        prevenido: false,
        returnValue: undefined,
        preventDefault() {
          this.prevenido = true;
        },
      };
      for (const e of escuchas) e.funcion(evento);
      return evento;
    },
  };
}

function estadoConFormulario(cambiar) {
  const formulario = Revision.formularioDe(valores(), catalogo());
  if (cambiar) formulario.descripcion = "Otra descripción de ejemplo";
  return { formulario };
}

test("f038 R13: la guarda de salida pide confirmación solo con una edición sin guardar", () => {
  const conCambios = montarGuarda({ alpine: { $data: () => estadoConFormulario(true) } });
  assert.deepEqual(conCambios.escuchas.map((e) => e.tipo), ["beforeunload"], "una sola escucha, la de beforeunload");
  const evento = conCambios.salir();
  assert.equal(evento.prevenido, true, "con cambios, pregunta");
  assert.equal(typeof evento.returnValue, "string", "y pone returnValue, que piden algunos navegadores");

  for (const [que, estado] of [
    ["sin formulario", { formulario: null }],
    ["con el formulario sin cambios", estadoConFormulario(false)],
  ]) {
    const guarda = montarGuarda({ alpine: { $data: () => estado } });
    const sinPregunta = guarda.salir();
    assert.equal(sinPregunta.prevenido, false, que);
    assert.equal(sinPregunta.returnValue, undefined, que);
  }
});

test("f038 R13: si no puede leer el estado, la guarda no pregunta ni lanza", () => {
  for (const [que, opciones] of [
    ["sin Alpine", {}],
    ["$data que lanza", { alpine: { $data: () => { throw new Error("ilegible"); } } }],
    ["sin la raíz del componente", { alpine: { $data: () => estadoConFormulario(true) }, raiz: null }],
  ]) {
    const guarda = montarGuarda(opciones);
    const evento = guarda.salir();
    assert.equal(evento.prevenido, false, que);
  }
});

test("f038 R13: la guarda lee el componente de la página por su x-data, no otro", () => {
  const pedidos = [];
  const escuchas = [];
  const ventana = { addEventListener: (tipo, funcion) => escuchas.push(funcion), Revision, Alpine: { $data: () => estadoConFormulario(true) } };
  const documento = { querySelector: (selector) => { pedidos.push(selector); return {}; } };
  require("node:vm").runInNewContext(guardaDeSalida(), { window: ventana, document: documento });
  escuchas[0]({ preventDefault() {}, returnValue: undefined });
  assert.deepEqual(pedidos, ['[x-data="appRevision()"]']);
});

// --- Correcciones de la review del Bloque 1 bis (C-B1b-1, C-B1b-2, O-B1b-2) ---------------------
//
// La guardia de texto (`puedeActuar()` aparece en el `:disabled`) no prueba la
// expresión: aquí cada `:disabled` de acción se evalúa con su tabla de verdad,
// en un alcance hijo SIN los bloqueos que fuerza `alcanceConTodoAbierto` (que
// taparían el término de `puedeActuar()`); cada clic de acción se EJECUTA y se
// mira que llegue a su fila; y los dos `x-show` que acompañan a las acciones
// se evalúan como el `:disabled` de «Aprobar».

/** Copia con un texto cambiado una sola vez; falla si el control ya no encuentra su ancla. */
function cambiarUnaVez(html, viejo, nuevo) {
  assert.equal(html.split(viejo).length, 2, `el control no encuentra una sola vez: ${viejo}`);
  return html.replace(viejo, nuevo);
}

/**
 * Cada botón de acción salvo «Aprobar» (que tiene su tabla aparte): el método
 * de su clic, el estado de la fila en que se pinta, cómo quitarle su bloqueo
 * propio, cómo ponérselo (o `null` si no tiene) y, si lo hay, un alcance en el
 * que el bloqueo propio NO aplica.
 */
const DISABLED_DE_CADA_BOTON = [
  {
    metodo: "abrirFormulario",
    estado: "nueva",
    sinBloqueo: (a) => { a.formulario = null; },
    conBloqueo: (a) => { a.formulario = Revision.formularioDe(valores(), catalogo()); },
  },
  {
    metodo: "pedirDescarte",
    estado: "nueva",
    sinBloqueo: (a) => { a.confirmandoDescarte = null; },
    conBloqueo: (a) => { a.confirmandoDescarte = a.fila.incidencia_id; },
    libreCon: (a) => { a.confirmandoDescarte = ID_2; },
  },
  { metodo: "confirmarDescarte", estado: "nueva", sinBloqueo: () => {}, conBloqueo: null },
  { metodo: "guardarEdicion", estado: "nueva", sinBloqueo: () => {}, conBloqueo: null },
  { metodo: "recuperar", estado: "descartada", sinBloqueo: () => {}, conBloqueo: null },
];

function botonesDelClic(elementos, metodo) {
  return elementos.filter(
    (e) => e.nombre === "button" && new RegExp(`^\\s*${metodo}\\(`).test(e.atributos["@click"] || ""),
  );
}

/** C-B1b-1 · lo que el `:disabled` de cada botón de acción incumple de su tabla de verdad. Vacío = correcto. */
async function problemasDelDisabled(html) {
  const problemas = [];
  const porEstado = {};
  for (const caso of DISABLED_DE_CADA_BOTON) {
    if (!porEstado[caso.estado]) {
      porEstado[caso.estado] = recorrerBandeja(html, await alcanceConTodoAbierto(caso.estado)).elementos;
    }
    const botones = botonesDelClic(porEstado[caso.estado], caso.metodo);
    if (botones.length !== 1) {
      problemas.push(`${caso.metodo}: ${botones.length} botones pintados en una ${caso.estado}`);
      continue;
    }
    const boton = botones[0];
    const expresion = boton.atributos[":disabled"];
    if (expresion === undefined) {
      problemas.push(`${caso.metodo}: sin :disabled`);
      continue;
    }
    const deshabilitado = (actua, preparar) => {
      const alcance = Object.create(boton.alcance);
      caso.sinBloqueo(alcance);
      if (preparar) preparar(alcance);
      alcance.puedeActuar = () => actua;
      try {
        return Boolean(evaluarEn(alcance, expresion));
      } catch (error) {
        return `lanza: ${error.message}`;
      }
    };
    if (deshabilitado(false) !== true) problemas.push(`${caso.metodo}: sin puedeActuar() se puede pulsar (R10)`);
    if (deshabilitado(true) !== false) problemas.push(`${caso.metodo}: con sesión y sin otro bloqueo, no se puede pulsar`);
    if (caso.conBloqueo) {
      if (deshabilitado(true, caso.conBloqueo) !== true) problemas.push(`${caso.metodo}: con su bloqueo propio, se puede pulsar`);
      if (deshabilitado(false, caso.conBloqueo) !== true) problemas.push(`${caso.metodo}: con su bloqueo y sin sesión, se puede pulsar`);
    }
    if (caso.libreCon && deshabilitado(true, caso.libreCon) !== false) {
      problemas.push(`${caso.metodo}: el bloqueo de otra fila lo deshabilita también en esta`);
    }
  }
  return problemas;
}

test("f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumple su tabla de verdad", async () => {
  assert.deepEqual(await problemasDelDisabled(leerBandeja()), []);
});

// Los seis supervivientes de la review del Bloque 1 bis, en memoria.
const MUTANTES_DEL_DISABLED = [
  ["M1 «Editar» sin la negación", ':disabled="!puedeActuar() || formulario !== null"', ':disabled="puedeActuar() || formulario !== null"'],
  ["M2 «Descartar» sin la negación", ':disabled="!puedeActuar() || confirmandoDescarte === fila.incidencia_id"', ':disabled="puedeActuar() || confirmandoDescarte === fila.incidencia_id"'],
  ["M3 «Recuperar» siempre deshabilitado", '@click="recuperar(fila.incidencia_id)" :disabled="!puedeActuar()"', '@click="recuperar(fila.incidencia_id)" :disabled="!puedeActuar() || true"'],
  ["M4 «Guardar cambios» siempre deshabilitado", '@click="guardarEdicion()" :disabled="!puedeActuar()"', '@click="guardarEdicion()" :disabled="!puedeActuar() || true"'],
  ["M5 «Editar» deshabilitado con el formulario cerrado", ':disabled="!puedeActuar() || formulario !== null"', ':disabled="!puedeActuar() || formulario === null"'],
  ["M11 «Sí, descartarla» siempre deshabilitado", '@click="confirmarDescarte(fila.incidencia_id)" :disabled="!puedeActuar()"', '@click="confirmarDescarte(fila.incidencia_id)" :disabled="!puedeActuar() || true"'],
];

for (const [nombre, viejo, nuevo] of MUTANTES_DEL_DISABLED) {
  test(`f038 R10 (C-B1b-1): control: ${nombre} salta`, async () => {
    const problemas = await problemasDelDisabled(cambiarUnaVez(leerBandeja(), viejo, nuevo));
    assert.notDeepEqual(problemas, [], `${nombre}: la tabla de verdad no lo ve`);
  });
}

/**
 * C-B1b-2 · cada botón de acción, con su clic EJECUTADO en el alcance del
 * componente (con el `api` doble que cuenta): las cuatro que escriben llegan a
 * `accionRevision` con SU fila y su acción; abrir el formulario y pedir el
 * descarte lo hacen sobre SU fila.
 */
const CLIC_DE_CADA_BOTON = [
  { metodo: "aprobar", estado: "nueva", accion: "aprobar" },
  { metodo: "recuperar", estado: "descartada", accion: "recuperar" },
  { metodo: "confirmarDescarte", estado: "nueva", accion: "descartar" },
  {
    metodo: "guardarEdicion",
    estado: "nueva",
    accion: "editar",
    preparar: (a) => { a.formulario.descripcion = "Otra descripción de ejemplo"; },
  },
  {
    metodo: "abrirFormulario",
    estado: "nueva",
    preparar: (a) => { a.formulario = null; },
    comprobar: (a) =>
      a.formulario && a.formulario.vigentes && a.formulario.vigentes.descripcion === valores().descripcion
        ? null
        : "no abre el formulario de su fila",
  },
  {
    metodo: "pedirDescarte",
    estado: "nueva",
    preparar: (a) => { a.confirmandoDescarte = null; },
    comprobar: (a) => (a.confirmandoDescarte === ID_1 ? null : `pide el descarte de «${a.confirmandoDescarte}», no de su fila`),
  },
];

const ACCION_DEVUELTA = () =>
  incidencia({ estado: "editada", revision_id: "00000000-0000-4000-8000-0000000000b2", motivos_no_aprobable: [] });

/** C-B1b-2 · lo que el clic de cada botón de acción no hace sobre su fila. Vacío = correcto. */
async function problemasDelClic(html) {
  const problemas = [];
  for (const caso of CLIC_DE_CADA_BOTON) {
    const alcance = await alcanceConTodoAbierto(caso.estado, {}, { accionRevision: ACCION_DEVUELTA });
    if (caso.preparar) caso.preparar(alcance);
    const botones = botonesDelClic(recorrerBandeja(html, alcance).elementos, caso.metodo);
    if (botones.length !== 1) {
      problemas.push(`${caso.metodo}: ${botones.length} botones pintados en una ${caso.estado}`);
      continue;
    }
    const boton = botones[0];
    const llamadas = LLAMADAS_DEL_ALCANCE.get(alcance);
    const antes = llamadas.length;
    try {
      await evaluarEn(boton.alcance, boton.atributos["@click"]);
    } catch (error) {
      problemas.push(`${caso.metodo}: el clic lanza (${error.message})`);
      continue;
    }
    if (caso.accion) {
      const acciones = llamadas.slice(antes).filter((l) => l.nombre === "accionRevision");
      const cuerpos = acciones.map((l) => `${l.args[0].accion} de ${l.args[0].incidencia_id}`);
      if (cuerpos.join() !== `${caso.accion} de ${ID_1}`) {
        problemas.push(`${caso.metodo}: manda [${cuerpos.join(", ")}], no «${caso.accion} de ${ID_1}»`);
      }
    } else {
      const fallo = caso.comprobar(boton.alcance);
      if (fallo) problemas.push(`${caso.metodo}: ${fallo}`);
      if (llamadas.slice(antes).some((l) => l.nombre === "accionRevision")) {
        problemas.push(`${caso.metodo}: manda una acción, y solo abre`);
      }
    }
  }
  return problemas;
}

test("f038 R10, R11 (C-B1b-2): cada botón de acción, pulsado, actúa sobre SU fila", async () => {
  assert.deepEqual(await problemasDelClic(leerBandeja()), []);
});

for (const [nombre, viejo, nuevo] of [
  ["M10 «Aprobar» con el argumento con errata", '@click="aprobar(fila.incidencia_id)"', '@click="aprobar(fila.incidencia_idd)"'],
  ["«Recuperar» sin su fila", '@click="recuperar(fila.incidencia_id)"', '@click="recuperar()"'],
  ["«Sí, descartarla» sobre la fila abierta por otro nombre", '@click="confirmarDescarte(fila.incidencia_id)"', '@click="confirmarDescarte(fila.id)"'],
  ["«Editar» con el argumento con errata", '@click="abrirFormulario(fila.incidencia_id)"', '@click="abrirFormulario(fila.incidencia)"'],
  ["«Descartar» con el argumento con errata", '@click="pedirDescarte(fila.incidencia_id)"', '@click="pedirDescarte(fila.incidenciaId)"'],
]) {
  test(`f038 R10 (C-B1b-2): control: ${nombre} salta`, async () => {
    const problemas = await problemasDelClic(cambiarUnaVez(leerBandeja(), viejo, nuevo));
    assert.notDeepEqual(problemas, [], `${nombre}: el clic ejecutado no lo ve`);
  });
}

/**
 * O-B1b-2 · los dos `x-show` que acompañan a las acciones, con su tabla de
 * verdad: el aviso de sesión incompleta (decisión 8) y «No se puede aprobar:
 * …» (R11). Se recorre una fila CON motivos, así que también se evalúan los
 * chips de motivos (O-B1b-1).
 */
async function problemasDeLosAvisos(html) {
  const problemas = [];
  const { elementos, problemas: deEvaluar } = recorrerBandeja(
    html,
    await alcanceConTodoAbierto("nueva", { motivos_no_aprobable: ["sin_ubicacion"] }),
  );
  problemas.push(...deEvaluar);

  const sesion = elementos.filter((e) => (e.atributos.class || "").split(/\s+/).includes("rs-aviso--info"));
  if (sesion.length !== 1 || !("x-show" in sesion[0].atributos)) {
    problemas.push(`el aviso de sesión incompleta: ${sesion.length} rs-aviso--info con x-show`);
  } else {
    for (const consulta of [null, { obra: "9901", estado: "activas" }]) {
      for (const usuarioOid of ["", OID]) {
        for (const correo of ["", CORREO]) {
          const alcance = Object.create(sesion[0].alcance);
          alcance.consulta = consulta;
          alcance.usuario = { usuarioOid, correo };
          const esperado = Boolean(consulta) && (!usuarioOid || !correo);
          if (Boolean(evaluarEn(alcance, sesion[0].atributos["x-show"])) !== esperado) {
            problemas.push(`aviso de sesión con consulta=${Boolean(consulta)}, oid=${Boolean(usuarioOid)}, correo=${Boolean(correo)}: se ve ≠ ${esperado}`);
          }
        }
      }
    }
  }

  const noAprobable = elementos.filter((e) => (e.atributos["x-text"] || "").includes("No se puede aprobar"));
  if (noAprobable.length !== 1 || !("x-show" in noAprobable[0].atributos)) {
    problemas.push(`«No se puede aprobar: …»: ${noAprobable.length} con x-show`);
  } else {
    const aviso = noAprobable[0];
    for (const [acciones, motivos, esperado] of [
      [["editar", "descartar", "aprobar"], ["Falta la ubicación"], true],
      [["editar", "descartar", "aprobar"], [], false],
      [["editar", "descartar"], ["Falta la ubicación"], false],
      [[], ["Falta la ubicación"], false],
    ]) {
      const alcance = Object.create(aviso.alcance);
      alcance.fila = Object.assign({}, aviso.alcance.fila, { acciones, motivos });
      if (Boolean(evaluarEn(alcance, aviso.atributos["x-show"])) !== esperado) {
        problemas.push(`«No se puede aprobar» con acciones=[${acciones}] y ${motivos.length} motivos: se ve ≠ ${esperado}`);
      }
    }
    if (!aviso.visible) problemas.push("«No se puede aprobar» no se ve en una nueva con motivos");
  }
  return problemas;
}

test("f038 R10, R11 (O-B1b-2): el aviso de sesión incompleta y «No se puede aprobar» se ven justo cuando toca", async () => {
  assert.deepEqual(await problemasDeLosAvisos(leerBandeja()), []);
});

for (const [nombre, viejo, nuevo] of [
  ["M13 el aviso de sesión con AND", 'x-show="consulta && (!usuario.usuarioOid || !usuario.correo)"', 'x-show="consulta && (!usuario.usuarioOid && !usuario.correo)"'],
  ["M15 «No se puede aprobar» oculto", "x-show=\"fila.acciones.includes('aprobar') && fila.motivos.length\"", 'x-show="false"'],
]) {
  test(`f038 R10, R11 (O-B1b-2): control: ${nombre} salta`, async () => {
    const problemas = await problemasDeLosAvisos(cambiarUnaVez(leerBandeja(), viejo, nuevo));
    assert.notDeepEqual(problemas, [], `${nombre}: la tabla de verdad no lo ve`);
  });
}

// --- Bloque 1 ter (T4 bis) · la presentación del volcado en bandeja.html (R21) -------------------
//
// Como el resto del recorrido: `bandeja.html` evaluada contra el componente de
// verdad, ahora con el `x-text` de cada elemento visible evaluado, con el
// detalle abierto y cerrado (cerrado, lo que se ve es la lista).

/** Los `x-text` evaluados de los elementos que se ven con ese alcance, y los elementos. */
function textosVisibles(html, alcance) {
  const { elementos, problemas } = recorrerBandeja(html, alcance);
  const textos = [];
  for (const e of elementos) {
    if (!e.visible || !("x-text" in e.atributos)) continue;
    try {
      textos.push(String(evaluarEn(e.alcance, e.atributos["x-text"])));
    } catch (error) {
      problemas.push(`x-text="${e.atributos["x-text"]}": ${error.message}`);
    }
  }
  return { textos, elementos, problemas };
}

function conElDetalleCerrado(alcance) {
  const cerrado = Object.create(alcance);
  cerrado.abierta = null;
  return cerrado;
}

const VOLCADO_RECHAZADO = objetoVolcado({ estado: "rechazado", sigrid_cod: null, motivo: "interviniente_ambiguo" });
const VOLCADO_NO_PROCESADO = objetoVolcado({ estado: "no_procesado", sigrid_cod: null, motivo: "presupuesto_de_tiempo_agotado" });

/**
 * Cada caso: el estado de la fila, su objeto `volcado`, la línea que tiene que
 * salir (o `null`), si sale también en la lista (R21.1, R21.2) o solo en el
 * detalle (R21.3) y si lleva «Ya no se revisa aquí» (R21.6).
 */
const CASOS_DEL_VOLCADO = [
  {
    que: "una volcada",
    estado: "volcada",
    volcado: objetoVolcado(),
    linea: "Volcada como RS99.99/0001 por " + CORREO + " el " + FECHA_DEL_VOLCADO,
    enLista: true,
  },
  {
    que: "una en duda con motivo",
    estado: "en_duda",
    volcado: objetoVolcado({ estado: "en_duda", sigrid_cod: null, motivo: "colision_de_clave" }),
    linea: LINEA_EN_DUDA + ". Motivo: Sigrid estaba creando otro parte a la vez: se puede volver a mandar sin riesgo",
    enLista: true,
  },
  {
    que: "una aprobada con el último intento rechazado",
    estado: "aprobada",
    volcado: VOLCADO_RECHAZADO,
    linea:
      "Último intento de volcado: no se creó el " + FECHA_DEL_VOLCADO + " por " + CORREO +
      ": El oficio tiene varios proveedores en la obra: hay que elegir uno",
    enLista: false,
  },
  {
    que: "una aprobada con el último intento sin procesar",
    estado: "aprobada",
    volcado: VOLCADO_NO_PROCESADO,
    linea:
      "Último intento de volcado: no se llegó a procesar el " + FECHA_DEL_VOLCADO + " por " + CORREO +
      ": Se acabó el tiempo antes de llegar a este parte: se puede volver a mandar sin riesgo",
    enLista: false,
  },
  { que: "una nueva sin volcado", estado: "nueva", volcado: null, linea: null, enLista: false },
];

const PRINCIPIO_DE_LINEA_DE_VOLCADO = /^(?:Volcada como |Se mandó a Sigrid |Último intento de volcado: )/;
const YA_NO_SE_REVISA = "Ya no se revisa aquí";

/** R21.1-R21.3, R21.6 · lo que la página no enseña (o enseña de más) del volcado. Vacío = correcto. */
async function problemasDelVolcadoEnLaPagina(html) {
  const problemas = [];
  const veces = (textos, texto) => textos.filter((t) => t === texto).length;
  for (const caso of CASOS_DEL_VOLCADO) {
    const alcance = await alcanceConTodoAbierto(caso.estado, { volcado: caso.volcado });
    const abierto = textosVisibles(html, alcance);
    const cerrado = textosVisibles(html, conElDetalleCerrado(alcance));
    problemas.push(...[...abierto.problemas, ...cerrado.problemas].map((p) => `${caso.que}: ${p}`));
    if (caso.linea) {
      const enLista = veces(cerrado.textos, caso.linea);
      const enDetalle = veces(abierto.textos, caso.linea) - enLista;
      if (enLista !== (caso.enLista ? 1 : 0)) {
        problemas.push(`${caso.que}: la línea del volcado sale ${enLista} veces en la lista, no ${caso.enLista ? 1 : 0}`);
      }
      if (enDetalle !== 1) problemas.push(`${caso.que}: la línea del volcado sale ${enDetalle} veces en el detalle, no 1`);
    }
    const otras = abierto.textos.filter((t) => PRINCIPIO_DE_LINEA_DE_VOLCADO.test(t) && t !== caso.linea);
    if (otras.length) problemas.push(`${caso.que}: líneas de volcado que no son la suya: ${otras.join(" | ")}`);
    const yaNoSeRevisa = ["volcada", "en_duda"].includes(caso.estado);
    const frase = veces(cerrado.textos, YA_NO_SE_REVISA);
    if (frase !== (yaNoSeRevisa ? 1 : 0)) {
      problemas.push(`${caso.que}: «${YA_NO_SE_REVISA}» sale ${frase} veces en la lista, no ${yaNoSeRevisa ? 1 : 0}`);
    }
    if (!cerrado.textos.includes(Revision.etiquetaEstado(caso.estado))) {
      problemas.push(`${caso.que}: no se ve su etiqueta «${Revision.etiquetaEstado(caso.estado)}»`);
    }
    if (yaNoSeRevisa) {
      const botones = abierto.elementos.filter((e) => e.nombre === "button" && e.visible && accionDelBoton(e));
      const campos = abierto.elementos.filter(
        (e) =>
          ["select", "textarea", "input"].includes(e.nombre) &&
          e.visible &&
          !/^(?:obra|filtros\.)/.test(e.atributos["x-model"] || ""),
      );
      if (botones.length || campos.length) {
        problemas.push(`${caso.que}: ${botones.length} botones de acción y ${campos.length} campos (R21.6: ninguno)`);
      }
      if (!abierto.textos.some((t) => t.startsWith("Importada el "))) {
        problemas.push(`${caso.que}: su historial no se lee (R21.6)`);
      }
      // C-B1t-1 · lista BLANCA: en la fila de una volcada o una en duda, lo
      // único que se pulsa es abrir o cerrar su detalle. Cualquier otro
      // <button> o <a> a la vista, con clic o sin él, es un problema.
      for (const [como, vista, permitido] of [
        ["con el detalle abierto", abierto, "cerrarDetalle()"],
        ["con el detalle cerrado", cerrado, "abrirDetalle(fila.incidencia_id)"],
      ]) {
        const pulsables = vista.elementos.filter(
          (e) => ["button", "a"].includes(e.nombre) && e.visible && "fila" in e.alcance,
        );
        const descritos = pulsables.map((e) => `<${e.nombre} @click="${e.atributos["@click"] || ""}">`);
        if (descritos.join() !== `<button @click="${permitido}">`) {
          problemas.push(
            `${caso.que}, ${como}: en la fila se puede pulsar [${descritos.join(", ")}], ` +
              `no solo <button @click="${permitido}"> (lista blanca de R21.6)`,
          );
        }
      }
    }
  }
  return problemas;
}

test("f038 R21.1-R21.3, R21.6: bandeja.html enseña la línea del volcado, la etiqueta y «Ya no se revisa aquí» donde toca", async () => {
  assert.deepEqual(await problemasDelVolcadoEnLaPagina(leerBandeja()), []);
});

for (const [nombre, viejo, nuevo] of [
  ["la línea de la lista sin su puerta (el último intento, en la lista)", 'x-show="fila.yaNoSeRevisa && fila.lineaVolcado"', 'x-show="fila.lineaVolcado"'],
  ["la línea de la lista oculta", 'x-show="fila.yaNoSeRevisa && fila.lineaVolcado"', 'x-show="false"'],
  ["la línea del detalle solo en volcada y en duda", 'x-show="fila.lineaVolcado"', 'x-show="fila.yaNoSeRevisa && fila.lineaVolcado"'],
  ["la línea del detalle con otro texto", 'x-show="fila.lineaVolcado" class="rs-texto" x-text="fila.lineaVolcado"', 'x-show="fila.lineaVolcado" class="rs-texto" x-text="fila.revisadoPor"'],
  ["«Ya no se revisa aquí» oculta", 'x-show="fila.yaNoSeRevisa"', 'x-show="false"'],
]) {
  test(`f038 R21 (T4 bis): control: ${nombre} salta`, async () => {
    const problemas = await problemasDelVolcadoEnLaPagina(cambiarUnaVez(leerBandeja(), viejo, nuevo));
    assert.notDeepEqual(problemas, [], `${nombre}: el recorrido no lo ve`);
  });
}

// C-B1t-1 · los tres supervivientes de la review del Bloque 1 ter (familia
// «botón que no hace nada»), metidos en la fila delante de la línea de la
// lista: un ancla que el mutante no repite. Tienen que caer en la LISTA BLANCA.
const ANCLA_DE_LA_FILA = '<p x-show="fila.yaNoSeRevisa && fila.lineaVolcado"';

for (const [nombre, intruso] of [
  ["H08b un botón sin clic en las volcadas", '<button x-show="!fila.acciones.length">Volcar otra vez</button>'],
  ["H08d un enlace en las volcadas", '<a x-show="!fila.acciones.length" href="#">Editar en Sigrid</a>'],
  [
    "H08e un botón con un clic ajeno en las volcadas",
    '<template x-if="!fila.acciones.length"><button @click="cerrarDetalle()" class="rs-btn rs-btn--ok">Volcar otra vez</button></template>',
  ],
]) {
  test(`f038 R21.6 (C-B1t-1): control: ${nombre} salta en la lista blanca`, async () => {
    const problemas = await problemasDelVolcadoEnLaPagina(
      cambiarUnaVez(leerBandeja(), ANCLA_DE_LA_FILA, intruso + "\n              " + ANCLA_DE_LA_FILA),
    );
    assert.ok(
      problemas.some((p) => p.includes("lista blanca de R21.6")),
      `${nombre}: la lista blanca no lo ve (${problemas.join(" | ")})`,
    );
  });
}
