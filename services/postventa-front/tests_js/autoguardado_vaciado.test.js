// services/postventa-front/tests_js/autoguardado_vaciado.test.js
// F-031 · El vaciado de lo pendiente antes de archivar (R18, R20, R21, R22).
//
// Por qué existe esto, en una frase: desde F-031 el backend **nombra el
// fichero con los códigos GUARDADOS** y coteja los del cuerpo. Quien corrija
// un código de obra y pulse «archivar y cerrar» antes de los 1.500 ms del
// rebote mandaría un código que todavía no está en la base, y se llevaría un
// 409 que no entiende. `requirements.md` §0.3 lo tiene medido: esa ventana es
// real y hoy nadie la cierra —`hayPendiente` existe desde F-026 y **no lo
// llama nadie**—.
//
// El arreglo es una sola pieza: `vaciarPendientes()`, que **fuerza** lo
// escrito y sin guardar y **espera** a que termine. `js/app.js` la llama antes
// de calcular la tanda; lo que se prueba aquí es la pieza, porque `app.js` es
// la única habitación de la casa sin tests (su propia cabecera lo dice).
//
// Las cuatro cosas que se fijan, y por qué cada una:
//
//   1. **Fuerza y espera** (R18). Sin la espera, el vaciado sería un «ya se
//      guardará» y la ventana del defecto seguiría abierta. Y vacía lo de
//      **cualquier** parte, no solo el que esté abierto: la tanda archiva
//      todos.
//   2. **Si no sale, lo dice y no se archiva** (R20). El vaciado devuelve
//      `{ok:false}` y `app.js` no lanza la tanda. Con un tope de rondas, que
//      no es adorno: `disparar` se reprograma cuando encuentra otro guardado
//      en vuelo y un bucle sin tope no terminaría nunca con alguien tecleando.
//   3. **Lo escrito no se pierde** (R21, F-026 R52 conservado). Forzar el
//      guardado no puede convertirse en la vía por la que se tira una
//      corrección que no se pudo escribir.
//   4. **Sin cambios, ni una petición** (R22). Pulsar «archivar y cerrar» sin
//      haber corregido nada no puede costar una escritura por parte contra un
//      PostgreSQL que comparten otros dos proyectos en producción.
//
// Va en fichero propio y no dentro de `autoguardado.test.js` para que el diff
// de F-031 se lea de un vistazo y para no engordar un fichero que ya cubre
// F-026 entera (`design.md` §2.1).
//
// Mismo planteamiento que el de F-026: temporizador **inyectado**, sin reloj
// real, sin DOM y sin red. TODOS los valores están INVENTADOS; los partes de
// verdad llevan DNI y observaciones manuscritas de clientes y no entran en el
// repositorio.

const test = require("node:test");
const assert = require("node:assert/strict");

const {
  crearAutoguardado,
  AVISO_SIN_GUARDAR,
  MENSAJE_FALLO,
  FALLO,
} = require("../js/autoguardado.js");

const HASH = "a1b2c3d4e5f6";
const OTRO_HASH = "f6e5d4c3b2a1";

/**
 * El mismo reloj de mentira que usa `autoguardado.test.js`.
 *
 * Aquí interesa sobre todo lo que **cancela**: el vaciado tiene que retirar el
 * rebote en espera antes de disparar, o el temporizador saltaría después de la
 * tanda y escribiría contra una remesa que ya está archivada.
 */
function relojFalso() {
  const reloj = {
    programados: [],
    cancelados: [],
    _siguienteId: 1,
    programar(fn, ms) {
      const id = reloj._siguienteId++;
      reloj.programados.push({ id: id, fn: fn, ms: ms, vivo: true, disparado: false });
      return id;
    },
    cancelar(id) {
      const encontrado = reloj.programados.find((uno) => uno.id === id);
      if (encontrado) {
        encontrado.vivo = false;
        reloj.cancelados.push(id);
      }
    },
    /** Los que llegarían a dispararse: los vivos y sin disparar. */
    vivos() {
      return reloj.programados.filter((uno) => uno.vivo && !uno.disparado);
    },
  };
  return reloj;
}

/** Un parte con sus nueve campos leídos por la IA, todos inventados. */
function parteInventado(hash) {
  return {
    hash: hash || HASH,
    ediciones: {},
    extraccion: {
      campos: {
        promocion: { valor: "PROMO-INVENTADA", confianza_pct: 90 },
        codigo_obra: { valor: "0677", confianza_pct: 88 },
        unidad: { valor: "3B", confianza_pct: 70 },
        numero_incidencia: { valor: "RS26.08/0123", confianza_pct: 95 },
        fecha_servicio: { valor: "2026-09-01", confianza_pct: 80 },
        descripcion: { valor: "texto inventado", confianza_pct: 60 },
        dni_cliente: { valor: "00000000T", confianza_pct: 55 },
        observaciones: { valor: "manuscrito inventado", confianza_pct: 30 },
        numero_pagina: { valor: "1", confianza_pct: 99 },
      },
    },
  };
}

/** Los valores del parte tal y como quedaron guardados la última vez. */
function valoresDe(parte) {
  const valores = {};
  Object.keys(parte.extraccion.campos).forEach(function (nombre) {
    valores[nombre] = parte.extraccion.campos[nombre].valor;
  });
  return valores;
}

/** Un autoguardado montado con reloj de mentira y un contador de guardados. */
function montar(ajustes) {
  const opciones = ajustes || {};
  const reloj = relojFalso();
  const guardados = [];
  const estados = [];
  const auto = crearAutoguardado({
    retardoMs: 1500,
    guardar: function (parte) {
      guardados.push(parte.hash);
      return opciones.guardar ? opciones.guardar(parte) : Promise.resolve({});
    },
    alCambiarEstado: function (cambio) {
      estados.push(cambio);
    },
    programar: reloj.programar,
    cancelar: reloj.cancelar,
  });
  return { auto: auto, reloj: reloj, guardados: guardados, estados: estados };
}

/** Deja correr las microtareas pendientes, sin tocar el reloj. */
async function respirar() {
  for (let tic = 0; tic < 30; tic += 1) {
    await Promise.resolve();
  }
}

/** Una promesa que resuelve cuando el test lo diga. */
function diferida() {
  const caja = {};
  caja.promesa = new Promise(function (resolver) {
    caja.resolver = resolver;
  });
  return caja;
}

/** Un parte recién guardado, con su corrección a medias ya tecleada. */
function conCorreccionSinGuardar(montaje, hash, nombre, valor) {
  const parte = parteInventado(hash);
  montaje.auto.anotarGuardado(parte, valoresDe(parte));
  parte.ediciones[nombre] = valor;
  montaje.auto.alEscribir(parte, nombre, valor);
  return parte;
}

// =========================================================================
// R18 · se fuerza lo escrito y se ESPERA
// =========================================================================

test("f031 R18: el vaciado no espera al rebote, fuerza el guardado y lo espera", async () => {
  // Éste es el caso del defecto, tal cual: corregir el código de obra y pulsar
  // «archivar y cerrar» dentro de los 1.500 ms. El reloj NO se corre en ningún
  // momento del test: si el guardado ocurre, es porque lo forzó el vaciado.
  const montaje = montar();
  const parte = conCorreccionSinGuardar(montaje, HASH, "codigo_obra", "0626");

  assert.equal(montaje.guardados.length, 0, "el rebote aún no ha saltado");

  const vaciado = await montaje.auto.vaciarPendientes();

  assert.equal(vaciado.ok, true);
  assert.deepEqual(montaje.guardados, [HASH]);
  // Y cuando la promesa resuelve, el guardado ya terminó: no queda nada
  // pendiente. Sin esta línea, «esperar» podría ser un «ya se guardará».
  assert.equal(montaje.auto.hayPendiente(parte), false);
});

test("f031 R18: el vaciado retira el rebote en espera en vez de dejarlo vivo", async () => {
  // Un temporizador que sobreviviera al vaciado saltaría DESPUÉS de la tanda y
  // escribiría contra un parte ya archivado. Es el mismo motivo por el que
  // `reiniciar()` llama a `cancelarPendiente` (F-026 R51).
  const montaje = montar();
  conCorreccionSinGuardar(montaje, HASH, "unidad", "4C");

  assert.equal(montaje.reloj.vivos().length, 1);

  await montaje.auto.vaciarPendientes();

  assert.equal(montaje.reloj.vivos().length, 0);
  assert.equal(montaje.reloj.cancelados.length >= 1, true);
});

test("f031 R18: con un guardado en vuelo, el vaciado espera a que termine", async () => {
  // La otra mitad de la ventana medida en `requirements.md` §0.3: pulsar
  // mientras la petición de guardado está en el aire. Si el vaciado no la
  // esperara, la tanda saldría con la base a medio escribir.
  const enVuelo = diferida();
  const montaje = montar({ guardar: () => enVuelo.promesa });
  const parte = conCorreccionSinGuardar(montaje, HASH, "codigo_obra", "0626");

  // Se dispara el rebote a mano y NO se espera: queda en vuelo.
  const pendiente = montaje.reloj.vivos()[0];
  pendiente.disparado = true;
  const guardadoEnVuelo = pendiente.fn();
  await respirar();
  assert.deepEqual(montaje.guardados, [HASH], "el guardado está en el aire");

  let terminado = false;
  const vaciado = montaje.auto.vaciarPendientes().then(function (resultado) {
    terminado = true;
    return resultado;
  });
  await respirar();

  assert.equal(terminado, false, "el vaciado no puede darse por bueno con un guardado en vuelo");

  enVuelo.resolver({});
  await guardadoEnVuelo;
  const resultado = await vaciado;

  assert.equal(resultado.ok, true);
  // Y no se guardó dos veces: esperar al que estaba en vuelo es justo lo que
  // evita la segunda escritura contra la base compartida.
  assert.deepEqual(montaje.guardados, [HASH]);
  assert.equal(montaje.auto.hayPendiente(parte), false);
});

test("f031 R18: se vacía lo pendiente de CUALQUIER parte, no solo del abierto", async () => {
  // La tanda archiva todos los partes pendientes del circuito, no el que esté
  // abierto. Un vaciado que solo mirase el parte en pantalla dejaría al resto
  // con la corrección sin escribir y el 409 caería sobre ellos.
  let fallaElPrimero = true;
  const montaje = montar({
    guardar: function (parte) {
      if (parte.hash === HASH && fallaElPrimero) {
        fallaElPrimero = false;
        return Promise.reject(new Error("la base no responde, inventado"));
      }
      return Promise.resolve({});
    },
  });

  // El parte A se quedó pendiente porque su guardado se cayó; el B es el que
  // está abierto, con su corrección aún en el rebote.
  const a = conCorreccionSinGuardar(montaje, HASH, "codigo_obra", "0626");
  const b = conCorreccionSinGuardar(montaje, OTRO_HASH, "codigo_obra", "0999");
  await respirar();
  assert.equal(montaje.auto.hayPendiente(a), true, "A sigue sin guardarse");
  assert.equal(montaje.auto.hayPendiente(b), true, "B sigue en el rebote");

  const vaciado = await montaje.auto.vaciarPendientes();

  assert.equal(vaciado.ok, true);
  assert.equal(montaje.auto.hayPendiente(a), false);
  assert.equal(montaje.auto.hayPendiente(b), false);
  // Los dos hashes se guardaron durante el vaciado, no solo el último tecleado.
  assert.equal(montaje.guardados.filter((uno) => uno === HASH).length >= 2, true);
  assert.equal(montaje.guardados.includes(OTRO_HASH), true);
});

// =========================================================================
// R20 · si no sale, se dice y la tanda no se lanza
// =========================================================================

test("f031 R20: si el guardado se cae, el vaciado devuelve que NO", async () => {
  // `app.js` no lanza la tanda con esto. Que el vaciado se diera por bueno
  // sería lo peor de los dos mundos: el backend nombraría con el código viejo
  // y la persona creería que su corrección se aplicó.
  const montaje = montar({
    guardar: function () {
      return Promise.reject(new Error("la base no responde, inventado"));
    },
  });
  const parte = conCorreccionSinGuardar(montaje, HASH, "codigo_obra", "0626");

  const vaciado = await montaje.auto.vaciarPendientes();

  assert.equal(vaciado.ok, false);
  assert.equal(typeof vaciado.motivo, "string");
  assert.notEqual(vaciado.motivo, "", "un `ok:false` sin motivo no se puede pintar");
  assert.equal(montaje.auto.hayPendiente(parte), true);
  // Y el aviso de F-026 quedó puesto: la pantalla ya dice que no se ha
  // guardado, sin que el vaciado tenga que inventarse una segunda explicación.
  assert.equal(montaje.auto.estado(), FALLO);
});

test("f031 R20: el vaciado tiene tope de rondas y no se queda en bucle", async () => {
  // `disparar` se reprograma cuando encuentra otro guardado en vuelo. Sin
  // tope, alguien tecleando delante dejaría el vaciado dando vueltas y la
  // pantalla colgada sin decir nada. El tope es lo que convierte ese caso en
  // un `{ok:false}` que se pinta.
  const montaje = montar({
    guardar: function () {
      return Promise.reject(new Error("la base no responde, inventado"));
    },
  });
  conCorreccionSinGuardar(montaje, HASH, "codigo_obra", "0626");

  const vaciado = await montaje.auto.vaciarPendientes();

  assert.equal(vaciado.ok, false);
  assert.equal(
    montaje.guardados.length <= 3,
    true,
    `el vaciado reintentó ${montaje.guardados.length} veces: no hay tope`,
  );
  assert.equal(montaje.guardados.length >= 1, true, "ni siquiera lo intentó");
});

test("f031 R20: el aviso dice que no se ha archivado nada y se apoya en el de F-026", () => {
  // Dos explicaciones distintas del mismo hecho es lo que hace que nadie lea
  // ninguna. El aviso nuevo AÑADE lo único que F-026 no podía decir —que la
  // tanda no ha salido— y reutiliza el resto.
  assert.equal(typeof AVISO_SIN_GUARDAR, "string");
  assert.equal(AVISO_SIN_GUARDAR.includes(MENSAJE_FALLO), true);
  assert.match(AVISO_SIN_GUARDAR, /no se ha archivado/i);
});

// =========================================================================
// R21 · lo escrito se queda donde está, pase lo que pase
// =========================================================================

test("f031 R21: aunque el vaciado falle, lo que la persona escribió sigue ahí", async () => {
  // F-026 R52 conservado. Forzar el guardado no puede ser la vía por la que se
  // pierde una corrección: quien vea desaparecer lo que tecleó no vuelve a
  // fiarse de la pantalla.
  const montaje = montar({
    guardar: function () {
      return Promise.reject(new Error("la base no responde, inventado"));
    },
  });
  const parte = conCorreccionSinGuardar(montaje, HASH, "codigo_obra", "0626");

  await montaje.auto.vaciarPendientes();

  assert.deepEqual(parte.ediciones, { codigo_obra: "0626" });
  // Y sigue constando como pendiente, así que el siguiente intento lo reintenta
  // en vez de darlo por escrito.
  assert.equal(montaje.auto.hayPendiente(parte), true);
});

test("f031 R21: el vaciado correcto tampoco toca `ediciones` ni lo que leyó la IA", async () => {
  // Lo que leyó el modelo se queda intacto en `parte.extraccion` para que F-015
  // pueda evaluar el prompt contra lo que dijo la máquina, no contra lo que
  // corrigió una persona (F-026 R53).
  const montaje = montar();
  const parte = conCorreccionSinGuardar(montaje, HASH, "codigo_obra", "0626");

  await montaje.auto.vaciarPendientes();

  assert.deepEqual(parte.ediciones, { codigo_obra: "0626" });
  assert.equal(parte.extraccion.campos.codigo_obra.valor, "0677");
});

// =========================================================================
// R22 · sin cambios, ni una petición
// =========================================================================

test("f031 R22: sin nada escrito, el vaciado no dispara ni un guardado", async () => {
  // Pulsar «archivar y cerrar» sin haber corregido nada no puede costar una
  // escritura por parte contra un PostgreSQL compartido con albaranes. Es
  // exactamente lo que F-026 R51 evitó y lo que esta feature no puede deshacer.
  const montaje = montar();
  const parte = parteInventado();
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  const vaciado = await montaje.auto.vaciarPendientes();

  assert.equal(vaciado.ok, true);
  assert.deepEqual(montaje.guardados, []);
  assert.deepEqual(montaje.reloj.programados, []);
  // Y tampoco se pinta nada: no ha pasado nada que contar.
  assert.deepEqual(montaje.estados, []);
});

test("f031 R22: escribir y deshacer no deja nada que vaciar", async () => {
  // El criterio de «hay cambios» es el de F-026 y no se duplica aquí: lo que
  // decide es si queda ALGO distinto de lo guardado, no si alguien tecleó.
  const montaje = montar();
  const parte = parteInventado();
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  montaje.auto.alEscribir(parte, "unidad", "4C");
  montaje.auto.alEscribir(parte, "unidad", "3B"); // el valor que ya constaba

  const vaciado = await montaje.auto.vaciarPendientes();

  assert.equal(vaciado.ok, true);
  assert.deepEqual(montaje.guardados, []);
});

test("f031 R22: un segundo vaciado seguido no vuelve a escribir", async () => {
  // La tanda se confirma, falla la confirmación y se vuelve a pulsar: el
  // segundo vaciado se encuentra todo guardado y no cuesta ni una petición.
  const montaje = montar();
  conCorreccionSinGuardar(montaje, HASH, "codigo_obra", "0626");

  await montaje.auto.vaciarPendientes();
  assert.deepEqual(montaje.guardados, [HASH]);

  const segundo = await montaje.auto.vaciarPendientes();

  assert.equal(segundo.ok, true);
  assert.deepEqual(montaje.guardados, [HASH], "el segundo vaciado escribió otra vez");
});
