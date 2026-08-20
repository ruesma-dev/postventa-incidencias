// services/postventa-front/tests_js/test_config_timeout.test.js
// R21 y R19 · El front cabe en el presupuesto del proxy, y NO gana ni URL de
// backend ni CORS al desplegarse.
//
// El proxy de la Static Web App corta cualquier petición a los 45 s. Es un
// límite de la plataforma, no una elección nuestra. Contra ese tope, el
// escalonado que fija F-010 (D2):
//
//     la IA abandona a los 35 s  →  el front aborta a los 40  →  el proxy
//     corta a los 45
//
// Cada capa cede antes que la de fuera. Si el front esperase más que el proxy
// —como esperaba antes de F-010, con 180000 ms—, quien cortaría sería el
// proxy: el usuario vería un error que ni el front ni el backend han
// generado, la petición no se reintentaría, la plaza de la cola no se
// liberaría y la llamada a la IA seguiría viva por detrás gastando cuota.
//
// `config.js` no es un módulo CommonJS: asigna sobre `window`. Así que se
// carga como lo cargaría el navegador —evaluando el fichero de verdad con un
// `window` de mentira—, en vez de duplicar aquí sus valores, que es como se
// escriben tests que siguen en verde cuando el fichero ya dice otra cosa.

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

/** El presupuesto del proxy de la Static Web App, en milisegundos. */
const PRESUPUESTO_PROXY_MS = 45000;

/** Lo que espera el backend antes de rendirse, en milisegundos. */
const TIEMPO_IA_MS = 35000;

const RUTA_CONFIG = path.join(__dirname, "..", "js", "config.js");

/** Evalúa `config.js` igual que lo haría el navegador y devuelve su objeto. */
function cargarConfig() {
  const fuente = fs.readFileSync(RUTA_CONFIG, "utf8");
  const contexto = { window: {} };
  vm.createContext(contexto);
  vm.runInContext(fuente, contexto, { filename: "config.js" });
  return contexto.window.CONFIG_POSTVENTA;
}

test("f010 R21: el front aborta ANTES de que corte el proxy", () => {
  const config = cargarConfig();

  assert.ok(
    config.TIMEOUT_PETICION_MS < PRESUPUESTO_PROXY_MS,
    `TIMEOUT_PETICION_MS (${config.TIMEOUT_PETICION_MS}) no cabe en el ` +
      `presupuesto del proxy (${PRESUPUESTO_PROXY_MS})`,
  );
});

test("f010 R21: y DESPUÉS de que se rinda el backend", () => {
  const config = cargarConfig();

  // Si el front abortara antes que la IA, mataría peticiones que iban a
  // responder: el orden de las tres capas dejaría de tener sentido.
  assert.ok(
    config.TIMEOUT_PETICION_MS > TIEMPO_IA_MS,
    `TIMEOUT_PETICION_MS (${config.TIMEOUT_PETICION_MS}) aborta antes que la ` +
      `IA (${TIEMPO_IA_MS}): el escalonado va al revés`,
  );
});

test("f010 R21: el valor es el que fijó D2, 40 s", () => {
  assert.equal(cargarConfig().TIMEOUT_PETICION_MS, 40000);
});

test("f010 R21: el porqué del número está escrito al lado", () => {
  // Un número sin su razón es un número que alguien sube "porque un parte
  // tardaba", y descubre en producción que quien corta es el proxy.
  const fuente = fs.readFileSync(RUTA_CONFIG, "utf8");
  const comentario = fuente.slice(0, fuente.indexOf("TIMEOUT_PETICION_MS:"));

  assert.match(comentario, /45/);
  assert.match(comentario, /proxy/i);
  assert.match(comentario, /escalonado/i);
});

test("f010 R19: el front sigue llamando al mismo origen, sin URL de backend", () => {
  const config = cargarConfig();

  // La Static Web App enlaza la Function bajo el mismo origen: `/api`. Que
  // esto siga así es lo que hace que el despliegue NO obligue a tocar el
  // front, ni a mantener CORS, ni a pedir un token en el navegador.
  assert.equal(config.baseApi, "/api");
});

test("f010 R19: no aparece ninguna URL absoluta en la configuración", () => {
  const fuente = fs.readFileSync(RUTA_CONFIG, "utf8");
  const asignaciones = fuente
    .split("\n")
    .filter((linea) => !linea.trim().startsWith("//"))
    .join("\n");

  assert.ok(
    !/https?:\/\//.test(asignaciones),
    "config.js ha ganado una URL absoluta: eso es CORS y un origen distinto",
  );
});

test("f010 R22: los reintentos de lo transitorio siguen en pie", () => {
  const config = cargarConfig();

  // No regresión: bajar el tiempo de espera solo sirve si el timeout se sigue
  // tratando como error TRANSITORIO. Sin reintentos, lo único que habríamos
  // hecho es fallar antes.
  assert.ok(config.REINTENTOS >= 1);
  assert.equal(config.ESPERAS_MS.length, config.REINTENTOS);
});
