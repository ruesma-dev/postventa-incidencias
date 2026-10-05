// services/postventa-front/tests_js/importacion.test.js
// F-036 R50, R52 · La pagina de importacion: su logica pura y su componente.
//
// Todo inventado: obra 9999, oficios 9001…, unidades «Portal inventado». Ni
// una obra, un oficio ni un proveedor de verdad (`tests/test_f036_front.py`
// lo vigila). Ningun test abre red: el `api` del componente es un doble.

const test = require("node:test");
const assert = require("node:assert/strict");

const Importacion = require("../js/importacion.js");

// --- Content-Disposition -----------------------------------------------------

test("f036 R50: el nombre de la plantilla sale de Content-Disposition", () => {
  assert.equal(
    Importacion.nombreDeDisposicion(
      'attachment; filename="plantilla_incidencias_9999_20260930.xlsx"',
      "otro.xlsx",
    ),
    "plantilla_incidencias_9999_20260930.xlsx",
  );
});

test("f036 R50: Content-Disposition sin comillas, con filename* o sin nombre", () => {
  assert.equal(
    Importacion.nombreDeDisposicion("attachment; filename=plantilla_9999.xlsx", "x.xlsx"),
    "plantilla_9999.xlsx",
  );
  assert.equal(
    Importacion.nombreDeDisposicion(
      "attachment; filename*=UTF-8''plantilla%20a%C3%B1o.xlsx; filename=\"b.xlsx\"",
      "x.xlsx",
    ),
    "plantilla año.xlsx",
    "filename* manda sobre filename (RFC 6266)",
  );
  assert.equal(Importacion.nombreDeDisposicion("attachment", "por-defecto.xlsx"), "por-defecto.xlsx");
  assert.equal(Importacion.nombreDeDisposicion("", "por-defecto.xlsx"), "por-defecto.xlsx");
  assert.equal(Importacion.nombreDeDisposicion(null, "por-defecto.xlsx"), "por-defecto.xlsx");
});

test("f036 R50: un nombre con ruta no se cuela en la descarga", () => {
  assert.equal(
    Importacion.nombreDeDisposicion('attachment; filename="../../x/plantilla.xlsx"', "d.xlsx"),
    "plantilla.xlsx",
  );
  assert.equal(
    Importacion.nombreDeDisposicion('attachment; filename="..\\\\x\\\\plantilla.xlsx"', "d.xlsx"),
    "plantilla.xlsx",
  );
});

test("f036 R50: la plantilla sin disposicion se llama por su obra", () => {
  assert.equal(Importacion.nombrePorDefectoDePlantilla("9999"), "plantilla_incidencias_9999.xlsx");
});

// --- El Excel de errores, desde base64 (R65) ---------------------------------

test("f036 R65: el base64 se decodifica a los bytes exactos", () => {
  const bytes = Importacion.bytesDeBase64("UEsDBAABAv8=");

  assert.ok(bytes instanceof Uint8Array);
  assert.deepEqual([...bytes], [0x50, 0x4b, 0x03, 0x04, 0x00, 0x01, 0x02, 0xff]);
});

test("f036 R65: un base64 vacio son cero bytes", () => {
  assert.equal(Importacion.bytesDeBase64("").length, 0);
});

test("f036 R65: el Excel de errores sale como Blob xlsx con su nombre", async () => {
  const excel = Importacion.excelDeErrores({
    excel_errores: {
      nombre: "incidencias_9999_errores_20260930.xlsx",
      contenido_b64: "UEsDBA==",
    },
  });

  assert.equal(excel.nombre, "incidencias_9999_errores_20260930.xlsx");
  assert.ok(excel.blob instanceof Blob);
  assert.equal(excel.blob.type, Importacion.TIPO_XLSX);
  assert.deepEqual([...new Uint8Array(await excel.blob.arrayBuffer())], [0x50, 0x4b, 0x03, 0x04]);
});

test("f036 R69: sin filas con error no hay Excel de errores", () => {
  assert.equal(Importacion.excelDeErrores({ estado: "completa" }), null);
  assert.equal(Importacion.excelDeErrores(null), null);
});

test("f036: el tipo es el de un .xlsx", () => {
  assert.equal(
    Importacion.TIPO_XLSX,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  );
});

// --- El resultado de la importacion (R43, R50) --------------------------------

/** Una respuesta de `POST /api/importaciones` inventada (forma de B6-7). */
function respuestaParcial() {
  return {
    importacion_id: "importacion-inventada",
    obra: "9999",
    ya_importado: false,
    estado: "parcial",
    resumen: { leidas: 5, nuevas: 2, duplicadas_en_fichero: 1, ya_en_bandeja: 1, con_error: 1 },
    filas: [
      { fila: 2, estado: "nueva", incidencia_id: "i-2", duplicada_de_fila: null, existente_id: null, avisos: [] },
      { fila: 3, estado: "duplicada_en_fichero", incidencia_id: "i-3", duplicada_de_fila: 2, existente_id: null, avisos: [] },
      { fila: 4, estado: "con_error", incidencia_id: null, duplicada_de_fila: null, existente_id: null, avisos: [] },
      { fila: 5, estado: "ya_en_bandeja", incidencia_id: null, duplicada_de_fila: null, existente_id: "i-0", avisos: [] },
      {
        fila: 6,
        estado: "nueva",
        incidencia_id: "i-6",
        duplicada_de_fila: null,
        existente_id: null,
        avisos: ["Oficio con varios códigos en Sigrid: se elige en la revisión"],
      },
    ],
    errores: [
      { fila: 4, columna: "Unidad", problema: "no es una unidad de la obra" },
      { fila: 4, columna: "Descripción", problema: "pasa de 128 caracteres" },
    ],
    total_errores: 2,
    excel_errores: { nombre: "incidencias_9999_errores.xlsx", contenido_b64: "UEsDBA==" },
  };
}

test("f036 R43: el texto de cada estado de fila", () => {
  assert.equal(Importacion.textoDeFila({ estado: "nueva" }), "Nueva");
  assert.equal(
    Importacion.textoDeFila({ estado: "duplicada_en_fichero", duplicada_de_fila: 2 }),
    "Duplicada de la fila 2 del mismo fichero",
  );
  assert.equal(Importacion.textoDeFila({ estado: "ya_en_bandeja" }), "Ya estaba en la bandeja");
  assert.equal(Importacion.textoDeFila({ estado: "con_error" }), "Con error: no ha entrado");
  assert.equal(Importacion.textoDeFila({ estado: "otro_raro" }), "otro_raro");
});

test("f036 R43: el texto del estado de la importacion", () => {
  assert.match(Importacion.textoDelEstado({ estado: "completa", ya_importado: false }), /^Importación completa/);
  assert.match(Importacion.textoDelEstado({ estado: "parcial", ya_importado: false }), /^Importación parcial/);
  assert.match(
    Importacion.textoDelEstado({ estado: "completa", ya_importado: true }),
    /ya se había importado/,
  );
});

test("f036 R43: el resumen, en una frase y con los cinco numeros", () => {
  assert.equal(
    Importacion.resumenLegible(respuestaParcial().resumen),
    "5 filas leídas · 2 nuevas · 1 duplicada en el fichero · 1 ya en la bandeja · 1 con error",
  );
  assert.equal(
    Importacion.resumenLegible({ leidas: 1, nuevas: 0, duplicadas_en_fichero: 2, ya_en_bandeja: 0, con_error: 3 }),
    "1 fila leída · 0 nuevas · 2 duplicadas en el fichero · 0 ya en la bandeja · 3 con error",
  );
});

test("f036 R50: los errores se ordenan por fila y se leen «Fila N · columna X · problema»", () => {
  const errores = [
    { fila: 10, columna: "Unidad", problema: "p1" },
    { fila: 2, columna: "Oficio", problema: "p2" },
    { fila: 10, columna: "Descripción", problema: "p3" },
  ];

  const ordenados = Importacion.erroresOrdenados(errores);

  assert.deepEqual(ordenados.map((e) => e.problema), ["p2", "p1", "p3"], "estable dentro de la fila");
  assert.equal(Importacion.textoDelError(ordenados[0]), "Fila 2 · columna Oficio · p2");
  assert.notStrictEqual(ordenados, errores, "no reordena la lista de la respuesta");
  assert.deepEqual(errores.map((e) => e.problema), ["p1", "p2", "p3"]);
});

test("f036 R33: si la lista viene recortada, se dice cuantos hay y donde estan todos", () => {
  assert.equal(Importacion.avisoDeErroresRecortados({ errores: [{}, {}], total_errores: 2 }), "");
  assert.equal(
    Importacion.avisoDeErroresRecortados({ errores: new Array(200).fill({}), total_errores: 350 }),
    "Se enseñan los primeros 200 errores de 350: el Excel de errores los trae todos.",
  );
  assert.equal(Importacion.avisoDeErroresRecortados({}), "");
});

test("f036 R50: presentarImportacion lo deja todo listo para pintar", () => {
  const vista = Importacion.presentarImportacion(respuestaParcial());

  assert.equal(vista.obra, "9999");
  assert.equal(vista.estado, "parcial");
  assert.match(vista.estadoTexto, /parcial/);
  assert.equal(vista.resumenTexto.startsWith("5 filas leídas"), true);
  assert.deepEqual(
    vista.filas.map((f) => [f.fila, f.texto, f.avisos]),
    [
      [2, "Nueva", []],
      [3, "Duplicada de la fila 2 del mismo fichero", []],
      [4, "Con error: no ha entrado", []],
      [5, "Ya estaba en la bandeja", []],
      [6, "Nueva", ["Oficio con varios códigos en Sigrid: se elige en la revisión"]],
    ],
  );
  assert.deepEqual(vista.errores, [
    "Fila 4 · columna Unidad · no es una unidad de la obra",
    "Fila 4 · columna Descripción · pasa de 128 caracteres",
  ]);
  assert.equal(vista.hayExcelDeErrores, true);
  assert.equal(vista.avisoRecorte, "");
});

test("f036 R69: una importacion completa no ofrece Excel de errores", () => {
  const completa = Object.assign(respuestaParcial(), {
    estado: "completa",
    errores: [],
    total_errores: 0,
  });
  delete completa.excel_errores;

  const vista = Importacion.presentarImportacion(completa);

  assert.equal(vista.hayExcelDeErrores, false);
  assert.deepEqual(vista.errores, []);
});

test("f036: la frase del Excel de errores es la de design.md §9", () => {
  assert.equal(
    Importacion.FRASE_EXCEL_ERRORES,
    "Corrígelo y súbelo otra vez; lo que ya entró no se duplica.",
  );
});

// --- La bandeja (R45, R50, R93, R99) ------------------------------------------

function incidencia(extra) {
  return Object.assign(
    {
      incidencia_id: "i-1",
      importacion_id: "imp-1",
      fila_origen: 2,
      unidad_codigo: "U-1",
      unidad_nombre: "Portal inventado 1",
      ubicacion: "Cocina",
      descripcion: "Descripción inventada",
      detalle: null,
      oficio_codigo: "9001",
      oficio_nombre: "Oficio inventado A",
      oficio_ambiguo: false,
      proveedor_codigo: null,
      proveedor_nombre: null,
      proveedor_ambiguo: false,
      urgencia: "normal",
      listado: null,
      duplicada_de: null,
      creada_at_utc: "2026-09-30T10:00:00+00:00",
    },
    extra || {},
  );
}

test("f036 R50: una duplicada de la misma importacion se marca con la fila del original", () => {
  const filas = Importacion.filasDeBandeja([
    incidencia({ incidencia_id: "i-1", fila_origen: 2 }),
    incidencia({ incidencia_id: "i-2", fila_origen: 3, duplicada_de: "i-1" }),
  ]);

  assert.deepEqual(filas[0].marcas, []);
  assert.deepEqual(filas[1].marcas, ["duplicada de la fila 2"]);
});

test("f036 R50: una duplicada de otra importacion lo dice, y si el original no esta en la lista tambien", () => {
  const filas = Importacion.filasDeBandeja([
    incidencia({ incidencia_id: "i-1", importacion_id: "imp-nueva", fila_origen: 7, duplicada_de: "i-9" }),
    incidencia({ incidencia_id: "i-9", importacion_id: "imp-vieja", fila_origen: 4 }),
    incidencia({ incidencia_id: "i-3", importacion_id: "imp-nueva", fila_origen: 8, duplicada_de: "i-fuera" }),
  ]);

  assert.deepEqual(filas[0].marcas, ["duplicada de la fila 4 de otra importación"]);
  assert.deepEqual(filas[2].marcas, ["duplicada de una incidencia anterior"]);
});

test("f036 R93/R99: el oficio ambiguo se marca y se ensena sin codigo", () => {
  const [fila] = Importacion.filasDeBandeja([
    incidencia({ oficio_codigo: null, oficio_nombre: "Oficio inventado A", oficio_ambiguo: true }),
  ]);

  assert.deepEqual(fila.marcas, ["varios códigos en Sigrid: se elige en la revisión"]);
  assert.equal(fila.oficioTexto, "Oficio inventado A");
  assert.equal(Importacion.MARCA_OFICIO_AMBIGUO, "varios códigos en Sigrid: se elige en la revisión");
});

test("f036 R45: oficio y proveedor con su codigo, y la falta de ellos", () => {
  const [conTodo, sinNada] = Importacion.filasDeBandeja([
    incidencia({ proveedor_codigo: "P-1", proveedor_nombre: "Proveedor inventado" }),
    incidencia({ oficio_codigo: null, oficio_nombre: null }),
  ]);

  assert.equal(conTodo.oficioTexto, "Oficio inventado A (9001)");
  assert.equal(conTodo.proveedorTexto, "Proveedor inventado (P-1)");
  assert.equal(sinNada.oficioTexto, "—");
  assert.equal(sinNada.proveedorTexto, "—");
});

test("f036 R45: la fila de la bandeja conserva lo que llega y anade lo pintado", () => {
  const [fila] = Importacion.filasDeBandeja([incidencia()]);

  assert.equal(fila.incidencia_id, "i-1");
  assert.equal(fila.descripcion, "Descripción inventada");
  assert.equal(fila.unidad_nombre, "Portal inventado 1");
  assert.equal(Importacion.filasDeBandeja(undefined).length, 0);
});

// --- Mensajes de error (R52) --------------------------------------------------

test("f036 R52: el mensaje de un error es el que trae, o su texto", () => {
  assert.equal(Importacion.mensajeDeError({ mensaje: "texto del backend" }), "texto del backend");
  assert.equal(Importacion.mensajeDeError(new Error("otra cosa")), "otra cosa");
  assert.equal(Importacion.mensajeDeError(null), "Error desconocido.");
});

// --- guardarBlob: la descarga al disco ---------------------------------------

function entornoFalso() {
  const registro = { creados: [], revocados: [], clics: [], anadidos: [], quitados: [] };
  const documento = {
    body: {
      appendChild: (el) => registro.anadidos.push(el),
      removeChild: (el) => registro.quitados.push(el),
    },
    createElement: (etiqueta) => {
      const el = { etiqueta, href: "", download: "", click: () => registro.clics.push(el) };
      return el;
    },
  };
  const URLFalsa = {
    createObjectURL: (blob) => {
      registro.creados.push(blob);
      return "blob:inventado-" + registro.creados.length;
    },
    revokeObjectURL: (url) => registro.revocados.push(url),
  };
  return { entorno: { documento, URL: URLFalsa }, registro };
}

test("f036 R50: guardarBlob descarga con su nombre y libera la URL", () => {
  const { entorno, registro } = entornoFalso();
  const blob = new Blob(["x"]);

  Importacion.guardarBlob(blob, "plantilla.xlsx", entorno);

  assert.equal(registro.clics.length, 1);
  assert.equal(registro.clics[0].etiqueta, "a");
  assert.equal(registro.clics[0].download, "plantilla.xlsx");
  assert.equal(registro.clics[0].href, "blob:inventado-1");
  assert.deepEqual(registro.revocados, ["blob:inventado-1"], "sin revocar, el Blob vive hasta cerrar la pestaña");
  assert.equal(registro.anadidos.length, 1);
  assert.equal(registro.quitados.length, 1);
});

// --- El componente (con un api doble) -----------------------------------------

function apiDoble(guion) {
  const llamadas = [];
  const api = {};
  for (const nombre of ["identidad", "descargarPlantilla", "importarExcel", "bandeja"]) {
    api[nombre] = async (...args) => {
      llamadas.push({ nombre, args });
      const paso = guion[nombre];
      if (typeof paso === "function") {
        return paso(...args);
      }
      if (paso instanceof Error) {
        throw paso;
      }
      return paso;
    };
  }
  return { api, llamadas };
}

function componente(guion) {
  const { api, llamadas } = apiDoble(
    Object.assign(
      {
        identidad: { usuarioOid: "oid-inventado", correo: "" },
        bandeja: { obra: "9999", total: 0, incidencias: [] },
      },
      guion,
    ),
  );
  const guardados = [];
  const app = Importacion.crearAppImportacion({
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

test("f036 R50: el componente arranca pidiendo quien es el usuario", async () => {
  const { app, llamadas } = componente({});

  await app.iniciar();

  assert.equal(app.usuario.usuarioOid, "oid-inventado");
  assert.deepEqual(llamadas.map((l) => l.nombre), ["identidad"]);
});

test("f036 R50: descargar la plantilla guarda el fichero con el nombre del backend", async () => {
  const blob = new Blob(["PK"]);
  const { app, llamadas, guardados } = componente({
    descargarPlantilla: { blob, disposicion: 'attachment; filename="plantilla_incidencias_9999_20260930.xlsx"' },
  });
  app.obra = "  9999 ";

  await app.descargarPlantilla();

  assert.deepEqual(llamadas.map((l) => [l.nombre, l.args[0]]), [["descargarPlantilla", "9999"]]);
  assert.deepEqual(guardados.map((g) => g.nombre), ["plantilla_incidencias_9999_20260930.xlsx"]);
  assert.equal(guardados[0].blob, blob);
  assert.equal(app.descargandoPlantilla, false);
  assert.equal(app.errorPlantilla, "");
});

test("f036 R52: si la plantilla falla, se ensena el mensaje del backend y no se guarda nada", async () => {
  const { app, guardados } = componente({ descargarPlantilla: errorApi("ninguna obra con unidades") });
  app.obra = "9999";

  await app.descargarPlantilla();

  assert.equal(app.errorPlantilla, "ninguna obra con unidades");
  assert.equal(guardados.length, 0);
  assert.equal(app.descargandoPlantilla, false);
});

test("f036 R50: sin obra no se pide la plantilla", async () => {
  const { app, llamadas } = componente({});
  app.obra = "   ";

  assert.equal(app.puedeDescargarPlantilla(), false);
  await app.descargarPlantilla();

  assert.equal(llamadas.length, 0);
});

test("f036 R50: elegir un fichero lo guarda y limpia el resultado anterior", () => {
  const { app } = componente({});
  const libro = { name: "incidencias.xlsx" };
  app.resultado = { obra: "vieja" };
  app.errorImportacion = "de antes";

  app.alElegirFichero({ target: { files: [libro] } });

  assert.equal(app.fichero, libro);
  assert.equal(app.resultado, null);
  assert.equal(app.errorImportacion, "");

  app.alElegirFichero({ target: { files: [] } });
  assert.equal(app.fichero, null);
});

test("f036 R22: sin usuario identificado no se importa, y se dice por que", async () => {
  const { app, llamadas } = componente({ identidad: { usuarioOid: "", correo: "" } });
  await app.iniciar();
  app.fichero = { name: "incidencias.xlsx" };

  assert.equal(app.puedeImportar(), false);
  assert.match(app.motivoSinImportar(), /sesión/);
  await app.importar();

  assert.deepEqual(llamadas.map((l) => l.nombre), ["identidad"]);
});

test("f036 R50: sin fichero no se importa", async () => {
  const { app } = componente({});
  await app.iniciar();

  assert.equal(app.puedeImportar(), false);
  assert.match(app.motivoSinImportar(), /fichero/);
});

test("f036 R50: importar pinta el resultado, fija la obra y recarga su bandeja", async () => {
  const { app, llamadas } = componente({
    importarExcel: respuestaParcial(),
    bandeja: { obra: "9999", total: 1, incidencias: [incidencia()] },
  });
  await app.iniciar();
  const libro = { name: "incidencias.xlsx" };
  app.fichero = libro;

  assert.equal(app.puedeImportar(), true);
  assert.equal(app.motivoSinImportar(), "");
  await app.importar();

  assert.deepEqual(
    llamadas.map((l) => l.nombre),
    ["identidad", "importarExcel", "bandeja"],
  );
  assert.deepEqual(llamadas[1].args, [libro, "oid-inventado"]);
  assert.equal(llamadas[2].args[0], "9999");
  assert.equal(app.obra, "9999");
  assert.equal(app.resultado.estado, "parcial");
  assert.equal(app.bandeja.length, 1);
  assert.equal(app.bandejaObra, "9999");
  assert.equal(app.importando, false);
});

test("f036 R52: un rechazo del fichero ensena su motivo y NO se reintenta", async () => {
  const { app, llamadas } = componente({
    importarExcel: errorApi("El fichero no es la plantilla: ya no se admite el formato antiguo"),
  });
  await app.iniciar();
  app.fichero = { name: "viejo.xlsx" };

  await app.importar();

  assert.equal(app.errorImportacion, "El fichero no es la plantilla: ya no se admite el formato antiguo");
  assert.equal(app.resultado, null);
  assert.equal(
    llamadas.filter((l) => l.nombre === "importarExcel").length,
    1,
    "R52: una sola peticion; volver a importar lo decide quien importa",
  );
  assert.equal(app.importando, false);
});

test("f036 R52: mientras se importa, el boton no deja lanzar otra", async () => {
  let soltar = null;
  const { app, llamadas } = componente({
    importarExcel: () => new Promise((resolver) => { soltar = () => resolver(respuestaParcial()); }),
  });
  await app.iniciar();
  app.fichero = { name: "incidencias.xlsx" };

  const primera = app.importar();
  assert.equal(app.importando, true);
  assert.equal(app.puedeImportar(), false);
  await app.importar();
  soltar();
  await primera;

  assert.equal(llamadas.filter((l) => l.nombre === "importarExcel").length, 1);
});

test("f036 R65: el boton del Excel de errores guarda el fichero decodificado", async () => {
  const { app, guardados } = componente({ importarExcel: respuestaParcial() });
  await app.iniciar();
  app.fichero = { name: "incidencias.xlsx" };
  await app.importar();

  app.descargarExcelDeErrores();

  assert.equal(guardados.length, 1);
  assert.equal(guardados[0].nombre, "incidencias_9999_errores.xlsx");
  assert.deepEqual([...new Uint8Array(await guardados[0].blob.arrayBuffer())], [0x50, 0x4b, 0x03, 0x04]);
});

test("f036 R69: sin Excel de errores el boton no guarda nada", async () => {
  const completa = Object.assign(respuestaParcial(), { estado: "completa", errores: [], total_errores: 0 });
  delete completa.excel_errores;
  const { app, guardados } = componente({ importarExcel: completa });
  await app.iniciar();
  app.fichero = { name: "incidencias.xlsx" };
  await app.importar();

  app.descargarExcelDeErrores();

  assert.equal(guardados.length, 0);
});

test("f036 R45: cargar la bandeja pide la obra escrita y pinta sus filas", async () => {
  const { app, llamadas } = componente({
    bandeja: {
      obra: "9999",
      total: 2,
      incidencias: [
        incidencia({ incidencia_id: "i-1" }),
        incidencia({ incidencia_id: "i-2", fila_origen: 3, duplicada_de: "i-1" }),
      ],
    },
  });
  app.obra = " 9999 ";

  await app.cargarBandeja();

  assert.deepEqual(llamadas.map((l) => [l.nombre, l.args[0]]), [["bandeja", "9999"]]);
  assert.deepEqual(app.bandeja[1].marcas, ["duplicada de la fila 2"]);
  assert.equal(app.bandejaCargada, true);
  assert.equal(app.cargandoBandeja, false);
});

test("f036 R52: si la bandeja falla, se dice y se vacia lo que habia", async () => {
  const { app } = componente({ bandeja: errorApi("sin base de datos") });
  app.obra = "9999";
  app.bandeja = [{ incidencia_id: "vieja" }];

  await app.cargarBandeja();

  assert.equal(app.errorBandeja, "sin base de datos");
  assert.deepEqual(app.bandeja, []);
  assert.equal(app.cargandoBandeja, false);
});

test("f036 R45: sin obra no se pide la bandeja", async () => {
  const { app, llamadas } = componente({});
  app.obra = "";

  await app.cargarBandeja();

  assert.equal(llamadas.length, 0);
});

test("f036: el componente no expone nada que edite, descarte o apruebe incidencias (F-038)", () => {
  const { app } = componente({});
  const nombres = Object.keys(app).join(" ").toLowerCase();

  for (const prohibido of ["editar", "descartar", "aprobar", "rechazar", "cerrar", "archivar"]) {
    assert.ok(!nombres.includes(prohibido), `el componente tiene algo de «${prohibido}»`);
  }
});
