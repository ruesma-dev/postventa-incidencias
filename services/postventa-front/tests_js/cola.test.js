// services/postventa-front/tests_js/cola.test.js
// R7-R12 · El limitador de concurrencia.
//
// Es la pieza central de F-007 y el criterio de aceptación 3: «una remesa
// larga no dispara N peticiones a la vez». La remesa real de Mirasierra son
// 22 partes y cada parte cuesta DOS llamadas de IA, así que sin límite son 44
// peticiones simultáneas.
//
// Todo se prueba con promesas controladas a mano: ni un reloj real, ni un
// `setTimeout`, ni una petición. Un test de concurrencia que dependa de
// tiempos es un test que falla en la máquina de otro.

const test = require("node:test");
const assert = require("node:assert/strict");

const { ejecutarConLimite } = require("../js/cola.js");

/** Una promesa que se resuelve o rechaza cuando el test lo decide. */
function diferida() {
  let resolver;
  let rechazar;
  const promesa = new Promise((res, rej) => {
    resolver = res;
    rechazar = rej;
  });
  return { promesa, resolver, rechazar };
}

/** Cede el turno para que corran las continuaciones pendientes. */
function respirar() {
  return new Promise((res) => setImmediate(res));
}

/**
 * Fabrica `cantidad` tareas controladas y un observador del máximo simultáneo.
 * Devuelve `{tareas, mandos, vivas, maximo}`.
 */
function fabricarTareas(cantidad) {
  const mandos = [];
  const estado = { vivas: 0, maximo: 0 };
  const tareas = [];

  for (let i = 0; i < cantidad; i += 1) {
    const mando = diferida();
    mandos.push(mando);
    tareas.push(() => {
      estado.vivas += 1;
      estado.maximo = Math.max(estado.maximo, estado.vivas);
      return mando.promesa.finally(() => {
        estado.vivas -= 1;
      });
    });
  }

  return { tareas, mandos, estado };
}

test("f007 R7: nunca hay más tareas vivas que el límite", async () => {
  const { tareas, mandos, estado } = fabricarTareas(22); // la remesa de Mirasierra
  const pendiente = ejecutarConLimite(tareas, 3);

  await respirar();
  assert.equal(estado.vivas, 3, "arranca exactamente con las plazas del límite");

  // Se van resolviendo de una en una: la plaza libre la ocupa la siguiente.
  for (let i = 0; i < 22; i += 1) {
    mandos[i].resolver(`parte-${i}`);
    await respirar();
    assert.ok(estado.maximo <= 3, `máximo observado ${estado.maximo} > 3`);
  }

  const resultados = await pendiente;
  assert.equal(resultados.length, 22);
  assert.equal(estado.maximo, 3);
});

test("f007 R7: no arranca la siguiente hasta que una plaza queda libre", async () => {
  const { tareas, mandos, estado } = fabricarTareas(5);
  const pendiente = ejecutarConLimite(tareas, 2);

  await respirar();
  assert.equal(estado.vivas, 2);

  await respirar();
  assert.equal(estado.vivas, 2, "sin que termine ninguna, no entra una tercera");

  mandos[0].resolver("ok");
  await respirar();
  assert.equal(estado.vivas, 2, "entra la tercera al liberarse la plaza");

  mandos.forEach((m) => m.resolver("ok"));
  await pendiente;
});

test("f007 R7: un límite mayor que el número de tareas no rompe nada", async () => {
  const { tareas, mandos, estado } = fabricarTareas(2);
  const pendiente = ejecutarConLimite(tareas, 10);

  await respirar();
  assert.equal(estado.vivas, 2);

  mandos.forEach((m) => m.resolver("ok"));
  const resultados = await pendiente;

  assert.deepEqual(
    resultados.map((r) => r.valor),
    ["ok", "ok"],
  );
});

test("f007 R7: una lista vacía de tareas devuelve una lista vacía", async () => {
  assert.deepEqual(await ejecutarConLimite([], 3), []);
});

test("f007 R7: un límite menor que 1 es un error, no un «sin límite» silencioso", async () => {
  const tarea = () => Promise.resolve("ok");

  await assert.rejects(() => ejecutarConLimite([tarea], 0), /límite/i);
  await assert.rejects(() => ejecutarConLimite([tarea], -1), /límite/i);
  await assert.rejects(() => ejecutarConLimite([tarea], 1.5), /límite/i);
});

test("f007 R9: alTerminar se llama exactamente una vez por tarea", async () => {
  const { tareas, mandos } = fabricarTareas(4);
  const terminadas = [];

  const pendiente = ejecutarConLimite(tareas, 2, (indice, resultado) => {
    terminadas.push({ indice, ok: resultado.ok });
  });

  mandos.forEach((m, i) => m.resolver(`v${i}`));
  await pendiente;

  assert.equal(terminadas.length, 4, "una llamada por tarea, ni más ni menos");
  assert.deepEqual(
    terminadas.map((t) => t.indice).sort((a, b) => a - b),
    [0, 1, 2, 3],
  );
});

test("f007 R9: el progreso también avanza cuando un parte termina en error", async () => {
  const { tareas, mandos } = fabricarTareas(3);
  const terminadas = [];

  const pendiente = ejecutarConLimite(tareas, 3, (indice, resultado) => {
    terminadas.push({ indice, ok: resultado.ok });
  });

  mandos[0].resolver("ok");
  mandos[1].rechazar(new Error("el modelo no devolvió nada utilizable"));
  mandos[2].resolver("ok");
  await pendiente;

  assert.equal(terminadas.length, 3, "N llega a M aunque haya errores");
  assert.equal(terminadas.filter((t) => !t.ok).length, 1);
});

test("f007 R10: un error no para a los demás y viaja como resultado, no como excepción", async () => {
  const { tareas, mandos } = fabricarTareas(4);
  const pendiente = ejecutarConLimite(tareas, 2);

  mandos[0].rechazar(new Error("502 del backend"));
  mandos[1].resolver("bien");
  mandos[2].rechazar(new Error("413: el parte no cabe"));
  mandos[3].resolver("también bien");

  const resultados = await pendiente; // NO rechaza: un parte roto no tumba la remesa

  assert.deepEqual(
    resultados.map((r) => r.ok),
    [false, true, false, true],
  );
  assert.equal(resultados[0].error.message, "502 del backend");
  assert.equal(resultados[3].valor, "también bien");
});

test("f007 R10: una tarea que lanza de forma síncrona tampoco tumba la cola", async () => {
  const resultados = await ejecutarConLimite(
    [
      () => {
        throw new Error("fallo antes de la promesa");
      },
      () => Promise.resolve("la siguiente sigue corriendo"),
    ],
    2,
  );

  assert.equal(resultados[0].ok, false);
  assert.equal(resultados[0].error.message, "fallo antes de la promesa");
  assert.equal(resultados[1].valor, "la siguiente sigue corriendo");
});

test("f007 R10: los resultados salen en el orden de entrada aunque terminen desordenados", async () => {
  const { tareas, mandos } = fabricarTareas(4);
  const pendiente = ejecutarConLimite(tareas, 4);

  // Terminan al revés de como entraron.
  mandos[3].resolver("cuarta");
  mandos[1].resolver("segunda");
  mandos[2].resolver("tercera");
  mandos[0].resolver("primera");

  const resultados = await pendiente;

  assert.deepEqual(
    resultados.map((r) => r.valor),
    ["primera", "segunda", "tercera", "cuarta"],
  );
});

test("f007 R11: reintentar un parte suelto pasa por la misma cola y el mismo límite", async () => {
  // El reintento no es un camino aparte: es otra ejecución de la MISMA función.
  const { tareas, mandos, estado } = fabricarTareas(1);
  const pendiente = ejecutarConLimite(tareas, 3);

  await respirar();
  assert.equal(estado.vivas, 1);
  assert.ok(estado.maximo <= 3);

  mandos[0].resolver("reintentado");
  const resultados = await pendiente;
  assert.deepEqual(resultados, [{ ok: true, valor: "reintentado" }]);
});

test("f007 R12: una tarea que falla libera su plaza, no la deja ocupada para siempre", async () => {
  // Es la razón de ser del timeout de R12: una petición colgada acaba en
  // error, y ese error tiene que devolver la plaza a la cola.
  const { tareas, mandos, estado } = fabricarTareas(4);
  const pendiente = ejecutarConLimite(tareas, 2);

  await respirar();
  assert.equal(estado.vivas, 2);

  mandos[0].rechazar(new Error("AbortError: la petición pasó de 180000 ms"));
  await respirar();
  assert.equal(estado.vivas, 2, "la plaza liberada por el error la ocupa la siguiente");

  mandos.forEach((m) => m.resolver("ok"));
  const resultados = await pendiente;
  assert.equal(resultados.length, 4, "la remesa termina entera pese al timeout");
});

test("f007 R7: la cola no llama a una tarea más de una vez", async () => {
  const llamadas = [];
  const tareas = [0, 1, 2, 3, 4].map((i) => () => {
    llamadas.push(i);
    return Promise.resolve(i);
  });

  await ejecutarConLimite(tareas, 2);

  assert.deepEqual(llamadas.sort((a, b) => a - b), [0, 1, 2, 3, 4]);
  assert.equal(llamadas.length, 5);
});
