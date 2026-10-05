// services/postventa-front/tests_js/api.test.js
// R12, R23-R27 · El cliente HTTP: timeout, reintentos y clasificación del error.
//
// F-019 lo amplió a NUEVE endpoints y añadió aquí lo que un doble de `api`
// no puede decir: a qué ruta se llama de verdad, con qué método y con qué
// cabeceras. La review lo pidió tras cambiar `/remesa` por una ruta
// inexistente y ver la suite entera en verde.
//
// NI UN TEST ABRE RED. El `fetch` es siempre un doble inyectado y el
// temporizador también: así R23 se prueba en milisegundos, sin relojes falsos
// y sin que el resultado dependa de la máquina.

const test = require("node:test");
const assert = require("node:assert/strict");

const { crearApi, ErrorApi } = require("../js/api.js");

const CONFIG = {
  TIMEOUT_PETICION_MS: 180000,
  REINTENTOS: 2,
  ESPERAS_MS: [1000, 3000],
};

/**
 * Una respuesta de `fetch` de mentira.
 *
 * F-036 T21 · gana `blob()` y `headers.get()`, que son lo que lee la descarga
 * de la plantilla (binaria, con su nombre en `Content-Disposition`). Lo que ya
 * habia -`status`, `ok`, `text()`- no cambia.
 */
function respuesta(status, cuerpo, cabeceras) {
  const texto = typeof cuerpo === "string" ? cuerpo : JSON.stringify(cuerpo);
  const mapa = cabeceras || {};
  return {
    status: status,
    ok: status >= 200 && status < 300,
    text: async () => texto,
    blob: async () => new Blob([texto]),
    headers: {
      get: (nombre) => {
        const clave = Object.keys(mapa).find(
          (k) => k.toLowerCase() === String(nombre).toLowerCase(),
        );
        return clave === undefined ? null : mapa[clave];
      },
    },
  };
}

/**
 * Monta una API con dobles. Devuelve la API y los registros de lo ocurrido.
 *
 * @param {Array} guion Lo que devuelve `fetch` en cada llamada. Un elemento
 *        que sea `Error` se lanza en vez de devolverse.
 */
function apiDePrueba(guion, extra) {
  const llamadas = [];
  const esperas = [];
  const trazas = [];
  const temporizadores = [];

  const fetchFalso = async (url, opciones) => {
    llamadas.push({ url, opciones });
    const paso = guion[Math.min(llamadas.length - 1, guion.length - 1)];
    if (typeof paso === "function") {
      return paso(url, opciones);
    }
    if (paso instanceof Error) {
      throw paso;
    }
    return paso;
  };

  const api = crearApi(
    Object.assign(
      {
        baseApi: "/api",
        config: CONFIG,
        fetch: fetchFalso,
        esperar: async (ms) => {
          esperas.push(ms);
        },
        traza: (evento) => {
          trazas.push(evento);
        },
        programarTimeout: (ms, alDispararse) => {
          temporizadores.push({ ms, alDispararse, cancelado: false });
          const propio = temporizadores[temporizadores.length - 1];
          return () => {
            propio.cancelado = true;
          };
        },
      },
      extra || {},
    ),
  );

  return { api, llamadas, esperas, trazas, temporizadores };
}

// --- R27 · salud -----------------------------------------------------------

test("f007 R27: la pantalla consulta GET /api/health al cargar", async () => {
  const { api, llamadas } = apiDePrueba([
    respuesta(200, {
      servicio: "postventa-api",
      version: "0.0.0",
      entorno: "test",
      estado: "ok",
    }),
  ]);

  const datos = await api.salud();

  assert.equal(llamadas[0].url, "/api/health");
  assert.equal(llamadas[0].opciones.method, "GET");
  assert.equal(datos.estado, "ok");
});

// --- R27 / F-019 / F-009 · los DIEZ endpoints, uno a uno -------------------
//
// Eran seis hasta F-019, que anadio `registrarRemesa`, `guardarParte` y
// `cola`, y nueve hasta F-009, que anadio `cerrar`. El titulo de este bloque
// decia «los seis» **y solo comprobaba dos**, asi que prometia de mas incluso
// antes de quedarse corto.
//
// Que la lista se recorra entera no es cosmetico: la review de F-019 cambio la
// ruta `/remesa` por una inexistente y los 122 tests de entonces siguieron en
// verde, porque `persistencia.test.js` prueba `pipeline.js` contra un `api`
// **doble** y nadie miraba lo que `api.js` hace de verdad. En el entorno real
// eso es un 404 por remesa, ningun parte guardable y ningun parte archivable.

/** Un PDF de mentira: cuatro bytes que no son un parte de nadie. */
function ficheroInventado() {
  return new File([new Uint8Array([0x25, 0x50, 0x44, 0x46])], "parte-inventado.pdf");
}

const HASH_INVENTADO = "a1b2c3d4e5f6";

/** El cuerpo de `POST /api/remesa`, con todo inventado. */
function cuerpoDeRemesa() {
  return {
    nombre_origen: "Mirasierra-inventada.pdf",
    num_partes: 2,
    avisos: [],
  };
}

/** El cuerpo de `POST /api/parte`, con lo justo para que el cliente lo mande. */
function cuerpoDeParteInventado() {
  return {
    remesa_id: "remesa-inventada-de-test",
    parte: { hash: HASH_INVENTADO, origen: "Mirasierra-inventada.pdf" },
    extraccion: { hash_parte: HASH_INVENTADO },
    firma: { hash_parte: HASH_INVENTADO },
  };
}

/** El cuerpo de `POST /api/cerrar`, con todo inventado y SIN commit. */
function cuerpoDeCierreInventado() {
  return {
    hash: HASH_INVENTADO,
    numero_incidencia: "RS26.08 - 0123",
    veredicto: "apto",
    destino: "archivo_y_cierre",
    estado_archivo: "archivado",
    usuario_oid: "oid-inventado-para-el-test",
  };
}

/**
 * El cuerpo de `POST /api/estado`: el de guardar mas las cuatro claves de F-028.
 *
 * Enmienda del 2026-09-16 · F-028 T16. Antes habia aqui un
 * `cuerpoDeAprobacionInventado` para `POST /api/aprobar`, que F-028 T15 retiro
 * del backend: ese endpoint devuelve 404 desde aquel commit. Lo que se prueba
 * sigue siendo lo mismo -que el cliente llama a SU ruta, con su metodo, su
 * cabecera y su paso propio de traza-, y por eso los tres casos de `aprobar`
 * se han reescrito sobre `cambiarEstado` en vez de borrarse.
 */
function cuerpoDeCambioDeEstadoInventado() {
  return Object.assign(cuerpoDeParteInventado(), {
    estado: "rechazado",
    usuario_oid: "oid-inventado-para-el-test",
    confirmado: true,
    motivo: "Inventado: la firma no es del cliente",
  });
}

/** Todos, con su ruta y su metodo. La lista ES la asercion. */
const LOS_ENDPOINTS = [
  { nombre: "salud", ruta: "/api/health", metodo: "GET", llamar: (api) => api.salud() },
  { nombre: "trocear", ruta: "/api/split", metodo: "POST", llamar: (api) => api.trocear(new FormData()) },
  { nombre: "extraer", ruta: "/api/extraer", metodo: "POST", llamar: (api) => api.extraer(ficheroInventado(), HASH_INVENTADO) },
  { nombre: "firma", ruta: "/api/firma", metodo: "POST", llamar: (api) => api.firma(ficheroInventado(), HASH_INVENTADO) },
  { nombre: "validar", ruta: "/api/validar", metodo: "POST", llamar: (api) => api.validar({ extraccion: {}, firma: {} }, HASH_INVENTADO) },
  { nombre: "registrarRemesa", ruta: "/api/remesa", metodo: "POST", llamar: (api) => api.registrarRemesa(cuerpoDeRemesa()) },
  { nombre: "guardarParte", ruta: "/api/parte", metodo: "POST", llamar: (api) => api.guardarParte(cuerpoDeParteInventado(), HASH_INVENTADO) },
  { nombre: "cola", ruta: "/api/cola", metodo: "GET", llamar: (api) => api.cola() },
  { nombre: "archivar", ruta: "/api/archivar", metodo: "POST", llamar: (api) => api.archivar(new FormData(), HASH_INVENTADO) },
  { nombre: "cerrar", ruta: "/api/cerrar", metodo: "POST", llamar: (api) => api.cerrar(cuerpoDeCierreInventado(), HASH_INVENTADO) },
  { nombre: "adjuntar", ruta: "/api/adjuntar", metodo: "POST", llamar: (api) => api.adjuntar(new FormData(), HASH_INVENTADO) },
  { nombre: "cambiarEstado", ruta: "/api/estado", metodo: "POST", llamar: (api) => api.cambiarEstado(cuerpoDeCambioDeEstadoInventado(), HASH_INVENTADO) },
  // F-036 T21 · la entrada de incidencias y los oficios repetidos. Obra y
  // codigos inventados: ninguno es de una obra de verdad.
  { nombre: "descargarPlantilla", ruta: "/api/plantilla?obra=9999", metodo: "GET", llamar: (api) => api.descargarPlantilla("9999") },
  { nombre: "importarExcel", ruta: "/api/importaciones", metodo: "POST", llamar: (api) => api.importarExcel(libroInventado(), "oid-inventado-para-el-test") },
  { nombre: "bandeja", ruta: "/api/bandeja?obra=9999", metodo: "GET", llamar: (api) => api.bandeja("9999") },
  { nombre: "propuestasCatalogos", ruta: "/api/catalogos/propuestas?obra=9999", metodo: "GET", llamar: (api) => api.propuestasCatalogos("9999") },
  { nombre: "decidirCatalogos", ruta: "/api/catalogos/decisiones", metodo: "POST", llamar: (api) => api.decidirCatalogos(cuerpoDeDecisionInventado()) },
];

/** Un `.xlsx` de mentira: cuatro bytes que no son el libro de nadie. */
function libroInventado() {
  return new File([new Uint8Array([0x50, 0x4b, 0x03, 0x04])], "incidencias-inventadas.xlsx");
}

/** El cuerpo de `POST /api/catalogos/decisiones`, con todo inventado. */
function cuerpoDeDecisionInventado() {
  return {
    obra: "9999",
    usuario_oid: "oid-inventado-para-el-test",
    confirmado: true,
    decisiones: [{ catalogo: "oficio", codigos: ["9001", "9002"], decision: "mismo" }],
  };
}

test("f007 R27 / f019 / f009 / f012 / f028 / f036: los DIECISIETE endpoints llaman a su ruta, con su metodo", async () => {
  for (const endpoint of LOS_ENDPOINTS) {
    const { api, llamadas } = apiDePrueba([respuesta(200, {})]);

    await endpoint.llamar(api);

    assert.equal(llamadas.length, 1, `${endpoint.nombre}: una peticion, ni mas`);
    assert.equal(llamadas[0].url, endpoint.ruta, `${endpoint.nombre}: ruta`);
    assert.equal(
      llamadas[0].opciones.method,
      endpoint.metodo,
      `${endpoint.nombre}: metodo`,
    );
  }
});

test("f007 R27 / f036: son diecisiete, y la lista se entera si aparece otro", () => {
  // Enmienda del 2026-09-30 · F-036 T21: eran DOCE y pasan a DIECISIETE con
  // los cinco de la entrada de incidencias (`descargarPlantilla`,
  // `importarExcel`, `bandeja`, `propuestasCatalogos` y `decidirCatalogos`).
  // No se quita ninguno de los doce: la comparacion nombre a nombre de abajo
  // lo diria.
  //
  // El cliente expone ademas `peticion` y `cuerpoDeParte`, que son la
  // maquinaria, y desde F-009 `identidad`, que NO es un endpoint de este
  // backend: lo sirve el proxy de la Static Web App y por eso no cuelga de
  // `/api`. Eran diez hasta F-012, que anade `adjuntar`, y once hasta F-026,
  // que anade `aprobar`; la cuenta tuvo que cuadrar aqui antes de que el
  // metodo existiera, que es para lo que esta.
  //
  // Enmienda del 2026-09-16 · F-028 T16: siguen siendo DOCE, pero no los
  // mismos doce. `aprobar` se va con su endpoint (`POST /api/aprobar`, que el
  // backend retiro en T15) y entra `cambiarEstado` (`POST /api/estado`). Que
  // el numero no se mueva es justo el caso que esta lista existe para NO dejar
  // pasar en silencio, y por eso va tambien la comparacion nombre a nombre de
  // la linea siguiente.
  const { api } = apiDePrueba([respuesta(200, {})]);
  const auxiliares = ["peticion", "cuerpoDeParte", "identidad"];
  const endpoints = Object.keys(api).filter((k) => auxiliares.indexOf(k) === -1);

  assert.equal(endpoints.length, 17);
  assert.deepEqual(endpoints.sort(), LOS_ENDPOINTS.map((e) => e.nombre).sort());
});

test("f007 R27: todos cuelgan de baseApi, y baseApi es configurable", async () => {
  for (const endpoint of LOS_ENDPOINTS) {
    const { api, llamadas } = apiDePrueba([respuesta(200, {})], {
      baseApi: "/otro-prefijo",
    });

    await endpoint.llamar(api);

    assert.ok(
      llamadas[0].url.startsWith("/otro-prefijo/"),
      `${endpoint.nombre} no cuelga de baseApi: ${llamadas[0].url}`,
    );
  }
});

// --- F-019 · los tres endpoints de persistencia, en detalle ----------------

test("f019 R25: registrarRemesa manda POST /api/remesa con cuerpo JSON", async () => {
  const { api, llamadas } = apiDePrueba([
    respuesta(200, { remesa_id: "remesa-inventada", resultado: "creado" }),
  ]);

  const datos = await api.registrarRemesa(cuerpoDeRemesa());

  assert.equal(llamadas[0].url, "/api/remesa");
  assert.equal(llamadas[0].opciones.method, "POST");
  assert.equal(
    llamadas[0].opciones.headers["Content-Type"],
    "application/json",
    "sin esta cabecera el backend no parsea el cuerpo y responde 400",
  );
  assert.deepEqual(JSON.parse(llamadas[0].opciones.body), cuerpoDeRemesa());
  assert.equal(datos.remesa_id, "remesa-inventada");
});

test("f019 R26: guardarParte manda POST /api/parte con cuerpo JSON", async () => {
  const { api, llamadas } = apiDePrueba([
    respuesta(200, {
      hash_parte: HASH_INVENTADO,
      resultado_parte: "creado",
      resultado_validacion: "creado",
      avisos: [],
    }),
  ]);

  const datos = await api.guardarParte(cuerpoDeParteInventado(), HASH_INVENTADO);

  assert.equal(llamadas[0].url, "/api/parte");
  assert.equal(llamadas[0].opciones.method, "POST");
  assert.equal(llamadas[0].opciones.headers["Content-Type"], "application/json");
  assert.deepEqual(
    JSON.parse(llamadas[0].opciones.body),
    cuerpoDeParteInventado(),
    "el cuerpo viaja verbatim: quien lo compone es js/pipeline.js",
  );
  assert.equal(datos.resultado_parte, "creado");
});

test("f019 R26: guardarParte deja el hash en la traza, para seguir el parte", async () => {
  const { api, trazas } = apiDePrueba([respuesta(200, {})]);

  await api.guardarParte(cuerpoDeParteInventado(), HASH_INVENTADO);

  assert.equal(trazas[trazas.length - 1].hash, HASH_INVENTADO);
  assert.equal(trazas[trazas.length - 1].paso, "parte");
});

test("f019 R26: el cuerpo de guardarParte NO lleva bytes de PDF", async () => {
  // El cliente serializa lo que le den, asi que aqui se fija que lo que sale
  // por el cable no lleva el documento: vive en SharePoint y este servidor
  // tiene el disco compartido.
  const { api, llamadas } = apiDePrueba([respuesta(200, {})]);

  await api.guardarParte(cuerpoDeParteInventado(), HASH_INVENTADO);

  assert.ok(!llamadas[0].opciones.body.includes("JVBER"));
  assert.ok(!llamadas[0].opciones.body.includes("contenido_b64"));
});

test("f019: cola sin limite pide GET /api/cola, sin cadena de consulta", async () => {
  // Sin `limite`, el backend aplica 50. Mandar `?limite=undefined` seria un
  // 400, y mandar `?limite=` tambien.
  const { api, llamadas } = apiDePrueba([respuesta(200, { total: 0, entradas: [] })]);

  await api.cola();

  assert.equal(llamadas[0].url, "/api/cola");
  assert.equal(llamadas[0].opciones.method, "GET");
  assert.equal(llamadas[0].opciones.body, undefined, "un GET no lleva cuerpo");
});

test("f019: cola con limite lo pone en la cadena de consulta", async () => {
  const { api, llamadas } = apiDePrueba([respuesta(200, { total: 0, entradas: [] })]);

  await api.cola(25);

  assert.equal(llamadas[0].url, "/api/cola?limite=25");
});

test("f019: cola escapa el limite, asi que no se cuela un parametro de mas", async () => {
  // Es lo unico que ejercita el `encodeURIComponent`, y no es teorico: sin el,
  // un valor con `&` dentro anadiria una segunda clave a la consulta y el
  // backend leeria la ultima. Con el, el valor entero llega como UN parametro
  // -malformado, que el backend rechaza con un 400- en vez de como dos.
  const { api, llamadas } = apiDePrueba([respuesta(200, { total: 0, entradas: [] })]);

  await api.cola("25&limite=100000");

  assert.equal(llamadas[0].url, "/api/cola?limite=25%26limite%3D100000");
  assert.ok(
    !llamadas[0].url.includes("&limite="),
    "sin escapar, la consulta llevaria DOS 'limite' y mandaria el segundo",
  );
});

test("f019: los tres endpoints nuevos trazan su paso, y nada mas", async () => {
  // R28 de F-007 sigue mandando: por la traza solo pasan hash, paso, estado y
  // http. Los cuerpos de remesa y parte llevan datos del papel.
  const nuevos = [
    { llamar: (api) => api.registrarRemesa(cuerpoDeRemesa()), paso: "remesa" },
    {
      llamar: (api) => api.guardarParte(cuerpoDeParteInventado(), HASH_INVENTADO),
      paso: "parte",
    },
    { llamar: (api) => api.cola(25), paso: "cola" },
  ];

  for (const nuevo of nuevos) {
    const { api, trazas } = apiDePrueba([respuesta(200, {})]);

    await nuevo.llamar(api);
    const evento = trazas[trazas.length - 1];

    assert.equal(evento.paso, nuevo.paso);
    assert.deepEqual(
      Object.keys(evento).filter(
        (k) => ["hash", "paso", "estado", "http"].indexOf(k) === -1,
      ),
      [],
      `la traza de ${nuevo.paso} lleva claves de mas`,
    );
  }
});

test("f028: cambiarEstado manda POST /api/estado, con cuerpo JSON y su paso propio", async () => {
  // Un paso propio y no «parte»: el registro tiene que poder distinguir
  // «alguien guardo el parte» de «alguien decidio su estado», que es la unica
  // puerta por la que un parte entra -o deja de entrar- en el circuito del ERP.
  const { api, llamadas, trazas } = apiDePrueba([
    respuesta(200, {
      hash_parte: HASH_INVENTADO,
      resultado_estado: "cambiado",
      estado: { estado: "rechazado", decidido_por_persona: true },
    }),
  ]);

  const datos = await api.cambiarEstado(
    cuerpoDeCambioDeEstadoInventado(),
    HASH_INVENTADO,
  );

  assert.equal(llamadas[0].url, "/api/estado");
  assert.equal(llamadas[0].opciones.method, "POST");
  assert.equal(
    llamadas[0].opciones.headers["Content-Type"],
    "application/json",
    "sin esta cabecera el backend no parsea el cuerpo y responde 400",
  );
  assert.equal(trazas[trazas.length - 1].paso, "estado");
  assert.equal(trazas[trazas.length - 1].hash, HASH_INVENTADO);
  assert.equal(datos.estado.estado, "rechazado");
});

test("f028 R52: por la traza del cambio de estado no pasa ni el oid ni el motivo", async () => {
  // R28 de F-007 sigue mandando: hash, paso, estado y http, y nada mas. El
  // cuerpo de esta peticion lleva el identificador de una persona Y el motivo,
  // que es texto libre y puede llevar dentro el nombre de un cliente.
  const { api, trazas } = apiDePrueba([respuesta(200, {})]);

  await api.cambiarEstado(cuerpoDeCambioDeEstadoInventado(), HASH_INVENTADO);
  const evento = trazas[trazas.length - 1];

  assert.deepEqual(
    Object.keys(evento).filter(
      (k) => ["hash", "paso", "estado", "http"].indexOf(k) === -1,
    ),
    [],
  );
});

// --- R23 · transitorios: 502 y fallo de red --------------------------------

test("f007 R23: un 502 se reintenta 2 veces con esperas de 1 s y 3 s", async () => {
  const { api, llamadas, esperas } = apiDePrueba([
    respuesta(502, { error: "el modelo no dio nada utilizable" }),
  ]);

  await assert.rejects(
    () => api.salud(),
    (error) => {
      assert.ok(error instanceof ErrorApi);
      assert.equal(error.tipo, "transitorio");
      assert.equal(error.http, 502);
      return true;
    },
  );

  assert.equal(llamadas.length, 3, "un intento + 2 reintentos, ni uno más");
  assert.deepEqual(esperas, [1000, 3000], "backoff creciente, no bucle desnudo");
});

test("f007 R23: un fallo de conexión también se reintenta", async () => {
  const { api, llamadas, esperas } = apiDePrueba([
    new TypeError("Failed to fetch"),
  ]);

  await assert.rejects(() => api.salud(), (error) => {
    assert.equal(error.tipo, "transitorio");
    assert.equal(error.http, null);
    return true;
  });

  assert.equal(llamadas.length, 3);
  assert.deepEqual(esperas, [1000, 3000]);
});

test("f007 R23: si el reintento va bien, el usuario no ve ningún error", async () => {
  const { api, llamadas, esperas } = apiDePrueba([
    respuesta(502, { error: "transitorio" }),
    respuesta(200, { estado: "ok" }),
  ]);

  const datos = await api.salud();

  assert.deepEqual(datos, { estado: "ok" });
  assert.equal(llamadas.length, 2, "no se agotan los reintentos si el 2.º va bien");
  assert.deepEqual(esperas, [1000]);
});

// --- R24 · 400, 409 y 413 no se reintentan ---------------------------------

test("f007 R24: un 400 no se reintenta y muestra el error del backend", async () => {
  const { api, llamadas, esperas } = apiDePrueba([
    respuesta(400, { error: "falta el campo codigo_obra", avisos: ["sin obra"] }),
  ]);

  await assert.rejects(() => api.validar({ extraccion: {}, firma: {} }), (error) => {
    assert.equal(error.tipo, "peticion");
    assert.equal(error.http, 400);
    assert.equal(error.mensaje, "falta el campo codigo_obra");
    assert.deepEqual(error.avisos, ["sin obra"]);
    return true;
  });

  assert.equal(llamadas.length, 1, "un 400 no mejora repitiéndolo");
  assert.deepEqual(esperas, []);
});

test("f007 R24: un 413 no se reintenta y sale como error de petición", async () => {
  const { api, llamadas } = apiDePrueba([
    respuesta(413, { error: "el parte pasa de 15 MB" }),
  ]);

  await assert.rejects(() => api.salud(), (error) => {
    assert.equal(error.tipo, "peticion");
    assert.equal(error.http, 413);
    return true;
  });
  assert.equal(llamadas.length, 1);
});

test("f007 R24: un 409 sale como no_apto y no se reintenta", async () => {
  const { api, llamadas } = apiDePrueba([
    respuesta(409, { error: "el parte no es apto para archivo" }),
  ]);

  await assert.rejects(() => api.archivar(new FormData()), (error) => {
    assert.equal(error.tipo, "no_apto");
    assert.equal(error.http, 409);
    assert.equal(error.mensaje, "el parte no es apto para archivo");
    return true;
  });
  assert.equal(llamadas.length, 1);
});

test("f007 R24: sin campo `error`, el mensaje no queda vacío", async () => {
  const { api } = apiDePrueba([respuesta(400, { avisos: [] })]);

  await assert.rejects(() => api.salud(), (error) => {
    assert.ok(error.mensaje.length > 0);
    assert.match(error.mensaje, /400/);
    return true;
  });
});

// --- R25 · el 503 de archivar es la puerta de entorno, no un fallo ---------

test("f007 R25: un 503 en archivar dice que este entorno no archiva y no reintenta", async () => {
  const { api, llamadas, esperas } = apiDePrueba([
    respuesta(503, { error: "ARCHIVO_HABILITADO está apagado" }),
  ]);

  await assert.rejects(() => api.archivar(new FormData()), (error) => {
    assert.equal(error.tipo, "entorno");
    assert.equal(error.http, 503);
    assert.match(error.mensaje, /entorno no archiva/i);
    return true;
  });

  assert.equal(llamadas.length, 1, "la puerta de entorno no se ablanda insistiendo");
  assert.deepEqual(esperas, []);
});

// --- R26 · una respuesta que no es JSON ------------------------------------

test("f007 R26: una respuesta HTML sale como desconocido con su código HTTP", async () => {
  // La Static Web App o el proxy pueden devolver una página de error.
  const { api } = apiDePrueba([
    respuesta(200, "<!doctype html><html><body>Error</body></html>"),
  ]);

  await assert.rejects(() => api.salud(), (error) => {
    assert.equal(error.tipo, "desconocido");
    assert.equal(error.http, 200);
    assert.match(error.mensaje, /inesperada/i);
    assert.match(error.mensaje, /200/);
    return true;
  });
});

test("f007 R26: un error 500 con cuerpo HTML tampoco lanza excepción sin capturar", async () => {
  const { api, llamadas } = apiDePrueba([respuesta(500, "<html>500</html>")]);

  await assert.rejects(() => api.salud(), (error) => {
    assert.ok(error instanceof ErrorApi);
    assert.equal(error.http, 500);
    return true;
  });
  assert.equal(llamadas.length, 1);
});

test("f007 R26: un cuerpo vacío en un 200 también es respuesta inesperada", async () => {
  const { api } = apiDePrueba([respuesta(200, "")]);

  await assert.rejects(() => api.salud(), (error) => {
    assert.equal(error.tipo, "desconocido");
    return true;
  });
});

// --- R12 · timeout con AbortController -------------------------------------

test("f007 R12: cada petición se programa para abortar a los 180 s", async () => {
  const { api, temporizadores } = apiDePrueba([respuesta(200, { estado: "ok" })]);

  await api.salud();

  assert.equal(temporizadores.length, 1);
  assert.equal(temporizadores[0].ms, 180000);
  assert.equal(temporizadores[0].cancelado, true, "una petición que responde cancela su timeout");
});

test("f007 R12: la señal de aborto viaja en la petición", async () => {
  const { api, llamadas } = apiDePrueba([respuesta(200, {})]);

  await api.salud();

  assert.ok(llamadas[0].opciones.signal, "sin signal, el timeout no aborta nada");
  assert.equal(llamadas[0].opciones.signal.aborted, false);
});

test("f007 R12: al dispararse el timeout, la petición se aborta y es transitoria", async () => {
  let disparar = null;
  const guion = [
    (url, opciones) =>
      new Promise((_, rechazar) => {
        opciones.signal.addEventListener("abort", () => {
          const error = new Error("This operation was aborted");
          error.name = "AbortError";
          rechazar(error);
        });
      }),
  ];

  const { api, esperas } = apiDePrueba(guion, {
    programarTimeout: (ms, alDispararse) => {
      disparar = alDispararse;
      // Se dispara en cuanto el bucle de eventos respira: simula los 180 s.
      setImmediate(() => disparar());
      return () => {};
    },
  });

  await assert.rejects(() => api.salud(), (error) => {
    assert.equal(error.tipo, "transitorio");
    assert.match(error.mensaje, /tardó demasiado|no se pudo contactar/i);
    return true;
  });

  assert.deepEqual(esperas, [1000, 3000], "un timeout es transitorio: se reintenta");
});

// --- Los endpoints y su forma ----------------------------------------------

test("f007 R8: extraer y firma envían el fichero y el hash del parte", async () => {
  const { api, llamadas } = apiDePrueba([respuesta(200, { hash_parte: "a1b2" })]);
  const parte = new File([new Uint8Array([0x25, 0x50])], "parte-inventado.pdf");

  await api.extraer(parte, "a1b2c3");

  assert.equal(llamadas[0].url, "/api/extraer");
  assert.equal(llamadas[0].opciones.method, "POST");
  const cuerpo = llamadas[0].opciones.body;
  assert.deepEqual([...cuerpo.keys()].sort(), ["fichero", "hash"]);
  assert.equal(cuerpo.get("hash"), "a1b2c3");
});

test("f007 R8: firma usa su propio endpoint", async () => {
  const { api, llamadas } = apiDePrueba([respuesta(200, {})]);
  const parte = new File([new Uint8Array([0x25, 0x50])], "parte-inventado.pdf");

  await api.firma(parte, "a1b2c3");

  assert.equal(llamadas[0].url, "/api/firma");
});

test("f007 R17: validar va en JSON y no toca extraer ni firma", async () => {
  const { api, llamadas } = apiDePrueba([respuesta(200, { veredicto: "apto" })]);
  const cuerpo = { extraccion: { hash_parte: "a1b2c3" }, firma: { hash_parte: "a1b2c3" } };

  await api.validar(cuerpo);

  assert.equal(llamadas.length, 1, "revalidar es UNA petición, no tres");
  assert.equal(llamadas[0].url, "/api/validar");
  assert.equal(llamadas[0].opciones.headers["Content-Type"], "application/json");
  assert.deepEqual(JSON.parse(llamadas[0].opciones.body), cuerpo);
});

test("f007 R4: trocear envía el multipart de la remesa tal cual", async () => {
  const { api, llamadas } = apiDePrueba([respuesta(200, { total_partes: 3 })]);
  const cuerpo = new FormData();
  cuerpo.append("fichero_0", new File([new Uint8Array([1])], "a.pdf"));

  const datos = await api.trocear(cuerpo);

  assert.equal(llamadas[0].url, "/api/split");
  assert.equal(llamadas[0].opciones.body, cuerpo, "el FormData no se reconstruye");
  assert.equal(datos.total_partes, 3);
});

test("f007 R26: el multipart NO lleva Content-Type puesto a mano", async () => {
  // Ponerlo a mano rompe el `boundary` que genera el navegador y el backend
  // recibe un cuerpo que no sabe parsear.
  const { api, llamadas } = apiDePrueba([respuesta(200, {})]);

  await api.trocear(new FormData());

  const cabeceras = llamadas[0].opciones.headers || {};
  assert.ok(!("Content-Type" in cabeceras));
});

// --- R28 · la traza del cliente HTTP ---------------------------------------

test("f007 R28: la traza del cliente lleva solo hash, paso, estado y http", async () => {
  const { api, trazas } = apiDePrueba([respuesta(200, { estado: "ok" })]);

  await api.extraer(
    new File([new Uint8Array([1])], "parte-inventado.pdf"),
    "a1b2c3",
  );

  assert.ok(trazas.length >= 1);
  trazas.forEach((evento) => {
    assert.deepEqual(
      Object.keys(evento).filter(
        (k) => ["hash", "paso", "estado", "http"].indexOf(k) === -1,
      ),
      [],
      `la traza lleva claves de más: ${JSON.stringify(Object.keys(evento))}`,
    );
  });
  assert.equal(trazas[trazas.length - 1].paso, "extraer");
  assert.equal(trazas[trazas.length - 1].http, 200);
});

test("f007 R28: la traza de un error tampoco lleva el cuerpo de la respuesta", async () => {
  const DNI_INVENTADO = "00000000T";
  const { api, trazas } = apiDePrueba([
    respuesta(400, { error: `no se pudo leer ${DNI_INVENTADO}` }),
  ]);

  await assert.rejects(() => api.salud());

  assert.ok(!JSON.stringify(trazas).includes(DNI_INVENTADO));
});

// --- F-009 · el cierre en Sigrid, en detalle -------------------------------
//
// Es el unico endpoint del cliente que escribe en el ERP de produccion, y por
// eso se comprueba aparte lo que en los demas no hace falta: que por omision
// NO cierre, que el cuerpo no lleve bytes de PDF y que el 503 sea la puerta de
// entorno y no un fallo que se reintente.

test("f009: cerrar manda POST /api/cerrar con cuerpo JSON", async () => {
  const { api, llamadas } = apiDePrueba([
    respuesta(200, { estado: "dry_run_ok", dry_run: {} }),
  ]);

  const datos = await api.cerrar(cuerpoDeCierreInventado(), HASH_INVENTADO);

  assert.equal(llamadas[0].url, "/api/cerrar");
  assert.equal(llamadas[0].opciones.method, "POST");
  assert.equal(
    llamadas[0].opciones.headers["Content-Type"],
    "application/json",
  );
  assert.equal(datos.estado, "dry_run_ok");
});

test("f009: por omision el cuerpo NO pide commit, asi que no cierra nada", async () => {
  const { api, llamadas } = apiDePrueba([respuesta(200, {})]);

  await api.cerrar(cuerpoDeCierreInventado(), HASH_INVENTADO);
  const enviado = JSON.parse(llamadas[0].opciones.body);

  // Lo que se comprueba es que la clave **no viene**: el backend la trata
  // como falsa, y quien no la ponga a proposito no escribe en el ERP.
  assert.equal(enviado.commit, undefined);
  assert.equal(enviado.confirmado, undefined);
});

test("f009: el cuerpo de cerrar NO lleva bytes de PDF", async () => {
  const { api, llamadas } = apiDePrueba([respuesta(200, {})]);

  await api.cerrar(cuerpoDeCierreInventado(), HASH_INVENTADO);
  const enviado = llamadas[0].opciones.body;

  // Va como texto JSON y no como FormData: este endpoint no sube nada, solo
  // mueve un estado. Si algun dia alguien le colase el fichero, esto lo ve.
  assert.equal(typeof enviado, "string");
  assert.equal(enviado.includes("%PDF"), false);
});

test("f009: cerrar deja el hash en la traza, para seguir el parte", async () => {
  const { api, trazas } = apiDePrueba([respuesta(200, {})]);

  await api.cerrar(cuerpoDeCierreInventado(), HASH_INVENTADO);

  assert.equal(trazas[0].hash, HASH_INVENTADO);
  assert.equal(trazas[0].paso, "cerrar");
});

test("f009: un 503 en cerrar es la puerta de entorno y NO se reintenta", async () => {
  // Misma regla que en archivar (R25): insistir no ablanda una puerta. Y aqui
  // menos que en ningun otro sitio: lo que hay detras es el ERP.
  const { api, llamadas } = apiDePrueba([
    respuesta(503, { error: "CIERRE_HABILITADO no esta activado" }),
  ]);

  await assert.rejects(
    () => api.cerrar(cuerpoDeCierreInventado(), HASH_INVENTADO),
    (error) => {
      assert.ok(error instanceof ErrorApi);
      assert.equal(error.tipo, "entorno");
      return true;
    },
  );
  assert.equal(llamadas.length, 1);
});

test("f009: un 409 en cerrar llega como 'no_apto' con su motivo", async () => {
  // Es el codigo del parte que no consta archivado, del estado que no admite
  // cierre y del login sin confirmar. Los tres se arreglan haciendo algo, no
  // reintentando, y por eso no se reintentan.
  const { api, llamadas } = apiDePrueba([
    respuesta(409, { error: "el login «fulanito» no existe en el ERP" }),
  ]);

  await assert.rejects(
    () => api.cerrar(cuerpoDeCierreInventado(), HASH_INVENTADO),
    (error) => {
      assert.equal(error.tipo, "no_apto");
      assert.match(error.mensaje, /login/);
      return true;
    },
  );
  assert.equal(llamadas.length, 1);
});

// --- F-009 · quien es el usuario, para poder firmar el cierre --------------

const { identidadDe } = require("../js/api.js");

test("f009: el oid de Entra sale de los claims, no del userId de la SWA", () => {
  // `userId` es el identificador que la Static Web App inventa para la sesion.
  // El backend guarda el `oid` del directorio, y confundirlos haria que la
  // persona perdiera su login mapeado el dia que la SWA cambiara el suyo.
  const identidad = identidadDe({
    clientPrincipal: {
      userId: "id-inventado-de-la-swa",
      userDetails: "fulanito@ejemplo.invalido",
      claims: [
        {
          typ: "http://schemas.microsoft.com/identity/claims/objectidentifier",
          val: "oid-inventado-de-entra",
        },
      ],
    },
  });

  assert.equal(identidad.usuarioOid, "oid-inventado-de-entra");
  assert.equal(identidad.correo, "fulanito@ejemplo.invalido");
});

test("f009: sin claim de oid se cae al userId, que es mejor que nada", () => {
  const identidad = identidadDe({
    clientPrincipal: { userId: "id-inventado-de-la-swa", userDetails: "x@ejemplo.invalido" },
  });

  assert.equal(identidad.usuarioOid, "id-inventado-de-la-swa");
});

test("f009: el correo preferido de los claims gana a userDetails", () => {
  const identidad = identidadDe({
    clientPrincipal: {
      userId: "u",
      userDetails: "algo-que-no-es-un-correo",
      claims: [{ typ: "preferred_username", val: "fulanito@ejemplo.invalido" }],
    },
  });

  assert.equal(identidad.correo, "fulanito@ejemplo.invalido");
});

test("f009: sin sesion, la identidad sale vacia y no revienta", () => {
  // Es el caso de local, donde /.auth/me no existe. Con la identidad vacia el
  // boton de cerrar se queda deshabilitado, que es lo correcto, y el resto de
  // la pantalla sigue sirviendo.
  for (const datos of [null, undefined, {}, { clientPrincipal: null }]) {
    assert.deepEqual(identidadDe(datos), { usuarioOid: "", correo: "" });
  }
});

test("f009: identidad() pide /.auth/me, que NO va bajo el prefijo de la API", () => {
  // Lo sirve el proxy de la Static Web App, no este backend. Anteponerle
  // `/api` daria un 404 en produccion y nadie podria cerrar nada.
  const llamadas = [];
  const api = crearApi({
    config: CONFIG,
    fetch: async (url) => {
      llamadas.push(url);
      return respuesta(200, { clientPrincipal: { userId: "u", userDetails: "x@y.z" } });
    },
    traza: () => {},
  });

  return api.identidad().then((identidad) => {
    assert.deepEqual(llamadas, ["/.auth/me"]);
    assert.equal(identidad.usuarioOid, "u");
  });
});

test("f009: si el proxy no responde, identidad() devuelve vacio y no rompe la pantalla", () => {
  const api = crearApi({
    config: CONFIG,
    fetch: async () => {
      throw new Error("aqui no hay proxy");
    },
    traza: () => {},
  });

  return api.identidad().then((identidad) => {
    assert.deepEqual(identidad, { usuarioOid: "", correo: "" });
  });
});

// --- F-036 · la entrada de incidencias y los oficios repetidos ---------------
//
// Cinco endpoints nuevos (`design.md` §8 de F-036, con la forma real de los
// handlers: `progress/impl_F-036.md`, B6-7 y B6-18). Dos reglas que los de
// antes no tenian:
//
// - **R52 · el mensaje es el del backend**, tambien en un 503. En el circuito
//   de partes un 503 es la puerta de entorno de archivar y se pinta con un
//   texto fijo; aqui un 503 es «sin Sigrid o sin base», y el backend explica
//   cual. Tragarse ese texto por el fijo de archivar seria mentir.
// - **R52 · la importacion no se reintenta sola.** Ni un 502, ni la red, ni
//   el tiempo agotado. Un reintento no duplicaria nada (el `sha256` lo
//   impide), pero R52 lo prohibe: lo decide quien importa.

const DISPOSICION_INVENTADA =
  'attachment; filename="plantilla_incidencias_9999_20260930.xlsx"';

test("f036 R50: descargarPlantilla pide GET /api/plantilla y devuelve el binario con su disposicion", async () => {
  const { api, llamadas } = apiDePrueba([
    respuesta(200, "PK-libro-inventado", { "Content-Disposition": DISPOSICION_INVENTADA }),
  ]);

  const descarga = await api.descargarPlantilla("9999");

  assert.equal(llamadas.length, 1);
  assert.equal(llamadas[0].url, "/api/plantilla?obra=9999");
  assert.equal(llamadas[0].opciones.method, "GET");
  assert.equal(descarga.disposicion, DISPOSICION_INVENTADA);
  assert.ok(descarga.blob instanceof Blob, "el cuerpo es un Blob, no un JSON");
  assert.equal(await descarga.blob.text(), "PK-libro-inventado");
});

test("f036 R50: descargarPlantilla sin Content-Disposition devuelve la disposicion vacia", async () => {
  const { api } = apiDePrueba([respuesta(200, "PK-libro-inventado")]);

  const descarga = await api.descargarPlantilla("9999");

  assert.equal(descarga.disposicion, "");
});

test("f036: las rutas con obra la escapan, asi que no se cuela un parametro de mas", async () => {
  const casos = [
    { llamar: (api) => api.descargarPlantilla("99&obra=1"), url: "/api/plantilla?obra=99%26obra%3D1" },
    { llamar: (api) => api.bandeja("99&obra=1"), url: "/api/bandeja?obra=99%26obra%3D1" },
    { llamar: (api) => api.propuestasCatalogos("99&obra=1"), url: "/api/catalogos/propuestas?obra=99%26obra%3D1" },
  ];

  for (const caso of casos) {
    const { api, llamadas } = apiDePrueba([respuesta(200, {})]);

    await caso.llamar(api);

    assert.equal(llamadas[0].url, caso.url);
  }
});

test("f036 R45: bandeja con limite lo pone en la consulta", async () => {
  const { api, llamadas } = apiDePrueba([respuesta(200, { obra: "9999", total: 0, incidencias: [] })]);

  await api.bandeja("9999", 50);

  assert.equal(llamadas[0].url, "/api/bandeja?obra=9999&limite=50");
  assert.equal(llamadas[0].opciones.body, undefined, "un GET no lleva cuerpo");
});

test("f036 R43: importarExcel manda el fichero y usuario_oid en multipart, sin Content-Type a mano", async () => {
  const cuerpoRespuesta = { importacion_id: "id-inventado", obra: "9999", estado: "completa" };
  const { api, llamadas } = apiDePrueba([respuesta(200, cuerpoRespuesta)]);
  const libro = libroInventado();

  const datos = await api.importarExcel(libro, "oid-inventado-para-el-test");

  assert.equal(llamadas[0].url, "/api/importaciones");
  assert.equal(llamadas[0].opciones.method, "POST");
  assert.ok(llamadas[0].opciones.body instanceof FormData);
  assert.deepEqual([...llamadas[0].opciones.body.keys()].sort(), ["fichero", "usuario_oid"]);
  assert.equal(llamadas[0].opciones.body.get("usuario_oid"), "oid-inventado-para-el-test");
  assert.equal(llamadas[0].opciones.body.get("fichero").name, "incidencias-inventadas.xlsx");
  assert.equal(llamadas[0].opciones.headers, undefined, "el boundary lo pone el navegador");
  assert.deepEqual(datos, cuerpoRespuesta);
});

test("f036 R52: importarExcel NO se reintenta ante un 502", async () => {
  const { api, llamadas, esperas, trazas } = apiDePrueba([
    respuesta(502, { error: "el proxy no ha llegado al backend" }),
  ]);

  await assert.rejects(() => api.importarExcel(libroInventado(), "oid-inventado-para-el-test"), (error) => {
    assert.equal(error.http, 502);
    assert.equal(error.mensaje, "el proxy no ha llegado al backend");
    return true;
  });

  assert.equal(llamadas.length, 1, "R52: la importacion no se repite por su cuenta");
  assert.deepEqual(esperas, []);
  assert.ok(
    trazas.every((t) => t.estado !== "reintentando"),
    "la traza no puede decir que se reintenta lo que no se reintenta",
  );
});

test("f036 R52: importarExcel NO se reintenta si la red falla, y no dice «Reintentando»", async () => {
  const { api, llamadas, esperas } = apiDePrueba([new TypeError("Failed to fetch")]);

  await assert.rejects(() => api.importarExcel(libroInventado(), "oid-inventado-para-el-test"), (error) => {
    assert.equal(error.tipo, "transitorio");
    assert.equal(error.http, null);
    assert.doesNotMatch(error.mensaje, /reintentando/i);
    assert.match(error.mensaje, /no se ha reintentado/i);
    return true;
  });

  assert.equal(llamadas.length, 1);
  assert.deepEqual(esperas, []);
});

test("f036 R52: importarExcel NO se reintenta si se agota el tiempo", async () => {
  const guion = [
    (url, opciones) =>
      new Promise((_, rechazar) => {
        opciones.signal.addEventListener("abort", () => {
          const error = new Error("This operation was aborted");
          error.name = "AbortError";
          rechazar(error);
        });
      }),
  ];
  const { api, llamadas, esperas } = apiDePrueba(guion, {
    programarTimeout: (ms, alDispararse) => {
      setImmediate(() => alDispararse());
      return () => {};
    },
  });

  await assert.rejects(() => api.importarExcel(libroInventado(), "oid-inventado-para-el-test"), (error) => {
    assert.equal(error.tipo, "transitorio");
    assert.match(error.mensaje, /no se ha reintentado/i);
    return true;
  });

  assert.equal(llamadas.length, 1);
  assert.deepEqual(esperas, []);
});

for (const caso of [
  { http: 400, tipo: "peticion", error: "El fichero no es la plantilla: formato antiguo", codigo: "formato_antiguo" },
  { http: 413, tipo: "peticion", error: "El fichero pasa de 2 MiB: no se ha abierto.", codigo: null },
  { http: 409, tipo: "no_apto", error: "hay dos obras con ese código", codigo: "obra_ambigua" },
  { http: 503, tipo: "entorno", error: "no se ha podido hablar con Sigrid y no se ha podido importar el fichero", codigo: null },
]) {
  test(`f036 R52: un ${caso.http} en importarExcel ensena el mensaje del backend y no se reintenta`, async () => {
    const cuerpo = { error: caso.error };
    if (caso.codigo) {
      cuerpo.codigo = caso.codigo;
    }
    const { api, llamadas, esperas } = apiDePrueba([respuesta(caso.http, cuerpo)]);

    await assert.rejects(() => api.importarExcel(libroInventado(), "oid-inventado-para-el-test"), (error) => {
      assert.equal(error.http, caso.http);
      assert.equal(error.tipo, caso.tipo);
      assert.equal(error.mensaje, caso.error, "R52: el texto del backend, tal cual");
      assert.equal(error.codigo, caso.codigo);
      return true;
    });

    assert.equal(llamadas.length, 1);
    assert.deepEqual(esperas, []);
  });
}

test("f036 R52: un 503 de la entrada NO se confunde con la puerta de entorno de archivar", async () => {
  const casos = [
    (api) => api.descargarPlantilla("9999"),
    (api) => api.bandeja("9999"),
    (api) => api.propuestasCatalogos("9999"),
    (api) => api.decidirCatalogos(cuerpoDeDecisionInventado()),
  ];

  for (const llamar of casos) {
    const { api } = apiDePrueba([respuesta(503, { error: "sin base de datos, inventado" })]);

    await assert.rejects(() => llamar(api), (error) => {
      assert.equal(error.http, 503);
      assert.equal(error.mensaje, "sin base de datos, inventado");
      assert.doesNotMatch(error.mensaje, /entorno no archiva/i);
      return true;
    });
  }
});

test("f036: el 503 de archivar sigue siendo la puerta de entorno (no cambia nada de antes)", async () => {
  const { api } = apiDePrueba([respuesta(503, { error: "ARCHIVO_HABILITADO está apagado" })]);

  await assert.rejects(() => api.archivar(new FormData()), (error) => {
    assert.match(error.mensaje, /entorno no archiva/i);
    return true;
  });
});

test("f036 R50: un error de descargarPlantilla trae el mensaje y el codigo del backend, sin reintentar", async () => {
  const { api, llamadas, esperas } = apiDePrueba([
    respuesta(404, { error: "ninguna obra 9999 tiene unidades de posventa", codigo: "obra_sin_unidades" }),
  ]);

  await assert.rejects(() => api.descargarPlantilla("9999"), (error) => {
    assert.equal(error.http, 404);
    assert.equal(error.mensaje, "ninguna obra 9999 tiene unidades de posventa");
    assert.equal(error.codigo, "obra_sin_unidades");
    return true;
  });
  assert.equal(llamadas.length, 1);
  assert.deepEqual(esperas, []);
});

test("f036 R50: descargarPlantilla con la red caida no se reintenta y lo dice", async () => {
  const { api, llamadas, trazas } = apiDePrueba([new TypeError("Failed to fetch")]);

  await assert.rejects(() => api.descargarPlantilla("9999"), (error) => {
    assert.equal(error.tipo, "transitorio");
    assert.match(error.mensaje, /no se ha reintentado/i);
    return true;
  });
  assert.equal(llamadas.length, 1);
  assert.equal(trazas[trazas.length - 1].paso, "plantilla");
  assert.equal(trazas[trazas.length - 1].estado, "transitorio");
});

test("f036 R50: un error de descargarPlantilla que no es JSON sale como desconocido", async () => {
  const { api } = apiDePrueba([respuesta(500, "<html>error del proxy</html>")]);

  await assert.rejects(() => api.descargarPlantilla("9999"), (error) => {
    assert.equal(error.tipo, "desconocido");
    assert.equal(error.http, 500);
    assert.match(error.mensaje, /500/);
    return true;
  });
});

test("f036 R50: descargarPlantilla programa su timeout y lo cancela al responder", async () => {
  const { api, llamadas, temporizadores } = apiDePrueba([respuesta(200, "PK")]);

  await api.descargarPlantilla("9999");

  assert.equal(temporizadores.length, 1);
  assert.equal(temporizadores[0].ms, 180000);
  assert.equal(temporizadores[0].cancelado, true);
  assert.ok(llamadas[0].opciones.signal, "sin signal, el timeout no aborta nada");
});

test("f036 R88: decidirCatalogos manda el cuerpo JSON tal cual y no se reintenta", async () => {
  const { api, llamadas, esperas } = apiDePrueba([respuesta(502, { error: "proxy caido, inventado" })]);

  await assert.rejects(() => api.decidirCatalogos(cuerpoDeDecisionInventado()));

  assert.equal(llamadas.length, 1, "una decision es un acto de una persona: no se repite sola");
  assert.deepEqual(esperas, []);
  assert.equal(llamadas[0].url, "/api/catalogos/decisiones");
  assert.equal(llamadas[0].opciones.method, "POST");
  assert.equal(llamadas[0].opciones.headers["Content-Type"], "application/json");
  assert.deepEqual(JSON.parse(llamadas[0].opciones.body), cuerpoDeDecisionInventado());
});

test("f036 R45/R87: bandeja y propuestas son lecturas: un 502 si se reintenta", async () => {
  for (const llamar of [(api) => api.bandeja("9999"), (api) => api.propuestasCatalogos("9999")]) {
    const { api, llamadas, esperas } = apiDePrueba([
      respuesta(502, { error: "transitorio" }),
      respuesta(200, { obra: "9999" }),
    ]);

    const datos = await llamar(api);

    assert.equal(llamadas.length, 2);
    assert.deepEqual(esperas, [1000]);
    assert.equal(datos.obra, "9999");
  }
});

test("f036: los cinco trazan su paso propio, y nada mas que hash, paso, estado y http", async () => {
  const casos = [
    { llamar: (api) => api.descargarPlantilla("9999"), paso: "plantilla" },
    { llamar: (api) => api.importarExcel(libroInventado(), "oid-inventado-para-el-test"), paso: "importaciones" },
    { llamar: (api) => api.bandeja("9999"), paso: "bandeja" },
    { llamar: (api) => api.propuestasCatalogos("9999"), paso: "propuestas" },
    { llamar: (api) => api.decidirCatalogos(cuerpoDeDecisionInventado()), paso: "decisiones" },
  ];

  for (const caso of casos) {
    const { api, trazas } = apiDePrueba([respuesta(200, {})]);

    await caso.llamar(api);
    const evento = trazas[trazas.length - 1];

    assert.equal(evento.paso, caso.paso);
    assert.equal(evento.estado, "ok");
    assert.deepEqual(
      Object.keys(evento).filter((k) => ["hash", "paso", "estado", "http"].indexOf(k) === -1),
      [],
    );
  }
});

test("f036: clasificar deja el texto y el codigo del backend en el error", () => {
  const { clasificar } = require("../js/api.js");

  const error = clasificar(409, { error: "texto inventado", codigo: "obra_ambigua" });
  const sinCodigo = clasificar(400, { error: "otro texto" });
  const sinJson = clasificar(502, undefined);

  assert.equal(error.mensajeServicio, "texto inventado");
  assert.equal(error.codigo, "obra_ambigua");
  assert.equal(sinCodigo.codigo, null);
  assert.equal(sinJson.mensajeServicio, null);
  assert.equal(sinJson.codigo, null);
});
