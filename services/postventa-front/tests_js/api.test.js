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

/** Una respuesta de `fetch` de mentira. */
function respuesta(status, cuerpo) {
  return {
    status: status,
    ok: status >= 200 && status < 300,
    text: async () =>
      typeof cuerpo === "string" ? cuerpo : JSON.stringify(cuerpo),
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

// --- R27 / F-019 · los NUEVE endpoints, uno a uno --------------------------
//
// Eran seis hasta F-019, que anadio `registrarRemesa`, `guardarParte` y
// `cola`. El titulo de este bloque decia «los seis» **y solo comprobaba dos**,
// asi que prometia de mas incluso antes de quedarse corto.
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

/** Los nueve, con su ruta y su metodo. La lista ES la asercion. */
const LOS_NUEVE = [
  { nombre: "salud", ruta: "/api/health", metodo: "GET", llamar: (api) => api.salud() },
  { nombre: "trocear", ruta: "/api/split", metodo: "POST", llamar: (api) => api.trocear(new FormData()) },
  { nombre: "extraer", ruta: "/api/extraer", metodo: "POST", llamar: (api) => api.extraer(ficheroInventado(), HASH_INVENTADO) },
  { nombre: "firma", ruta: "/api/firma", metodo: "POST", llamar: (api) => api.firma(ficheroInventado(), HASH_INVENTADO) },
  { nombre: "validar", ruta: "/api/validar", metodo: "POST", llamar: (api) => api.validar({ extraccion: {}, firma: {} }, HASH_INVENTADO) },
  { nombre: "registrarRemesa", ruta: "/api/remesa", metodo: "POST", llamar: (api) => api.registrarRemesa(cuerpoDeRemesa()) },
  { nombre: "guardarParte", ruta: "/api/parte", metodo: "POST", llamar: (api) => api.guardarParte(cuerpoDeParteInventado(), HASH_INVENTADO) },
  { nombre: "cola", ruta: "/api/cola", metodo: "GET", llamar: (api) => api.cola() },
  { nombre: "archivar", ruta: "/api/archivar", metodo: "POST", llamar: (api) => api.archivar(new FormData(), HASH_INVENTADO) },
];

test("f007 R27 / f019: los NUEVE endpoints llaman a su ruta, con su metodo", async () => {
  for (const endpoint of LOS_NUEVE) {
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

test("f007 R27: son nueve, y la lista se entera si aparece un decimo", () => {
  // El cliente expone ademas `peticion` y `cuerpoDeParte`, que son la
  // maquinaria, no endpoints. Si manana hay un decimo endpoint y nadie toca
  // esta lista, la cuenta deja de cuadrar y este test lo dice.
  const { api } = apiDePrueba([respuesta(200, {})]);
  const auxiliares = ["peticion", "cuerpoDeParte"];
  const endpoints = Object.keys(api).filter((k) => auxiliares.indexOf(k) === -1);

  assert.equal(endpoints.length, 9);
  assert.deepEqual(endpoints.sort(), LOS_NUEVE.map((e) => e.nombre).sort());
});

test("f007 R27: todos cuelgan de baseApi, y baseApi es configurable", async () => {
  for (const endpoint of LOS_NUEVE) {
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
