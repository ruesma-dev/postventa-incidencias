// services/postventa-front/tests_js/revision.test.js
// F-038 R3-R13, R22, R24 · La bandeja de revisión: lo puro y el componente.
//
// `specs/F-038-bandeja-revision/design.md` §2.4 y su tabla «Conciliado
// 2026-10-20», contra el contrato **implementado** del backend
// (`services/postventa-api/interface_adapters/api/revision.py` y
// `domain/models/revision.py`). La presentación del volcado (R21:
// `lineaDeVolcado`, `textoMotivoVolcado`, los filtros `volcada` y `en_duda`)
// es del Bloque 1 ter y NO se prueba aquí.
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
  // La línea del volcado (R21.1-R21.3) es del Bloque 1 ter: aquí solo que el
  // objeto no rompe la fila y que una volcada no ofrece nada.
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
