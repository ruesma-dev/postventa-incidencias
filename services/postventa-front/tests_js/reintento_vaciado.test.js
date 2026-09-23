// services/postventa-front/tests_js/reintento_vaciado.test.js
// F-034 · «Reintentar el cierre» guarda lo pendiente antes de escribir en el
// ERP (R29, R30, R31, R32, R33; hallazgo H-2 de `design.md` §8).
//
// Por qué existe esto, en una frase: desde F-034 el backend busca la
// reclamación y cierra la incidencia con el número **guardado**, y coteja el
// que viaja en el cuerpo. F-031 puso en `confirmarArchivo` el vaciado de lo
// escrito y sin guardar, pero `reintentarCierre` entraba al circuito con
// `_lanzarTanda([parte])` **sin pasar por él**: quien corrigiera el número de
// incidencia y pulsara «Reintentar el cierre» dentro de los 1.500 ms del
// rebote mandaba al ERP un número que la base todavía no tenía.
//
// A diferencia de `autoguardado_vaciado.test.js`, que prueba la pieza
// (`vaciarPendientes`), aquí se ejecuta **`js/app.js` de verdad**: el defecto
// no está en la pieza, está en que `reintentarCierre` no la llamaba. Un test
// sobre el texto fuente (como `test_f031_front.py`) diría que la llamada está
// escrita; este dice que se **espera** y que, si falla, **no sale nada**.
//
// Cómo se monta, sin navegador, sin red y sin reloj real:
//
//   - los módulos del front se cargan tal cual en un contexto de `node:vm`
//     cuyo `window` es el propio contexto, igual que en el navegador;
//   - `window.Api` es un **doble** que apunta cada petición en una sola lista
//     (`llamadas`), en orden: lo que se comprueba es el orden y el número;
//   - `setTimeout` es de mentira: el rebote del autoguardado **nunca salta**
//     solo, así que si hay un guardado es porque lo forzó el vaciado.
//
// Lo que NO se prueba aquí, porque ya tiene su sitio: el cuerpo de las
// peticiones (`circuito.test.js`, `cierre.test.js`, `grafico.test.js`), el
// vaciado en sí (`autoguardado_vaciado.test.js`) y la clasificación del 409
// (`api.test.js`).
//
// TODOS los valores están INVENTADOS: el código de obra, los números de
// incidencia, el `oid` y el correo, cuyo dominio no existe. Los partes de
// verdad llevan DNI y observaciones manuscritas de clientes y no entran en el
// repositorio.

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const RAIZ_JS = path.join(__dirname, "..", "js");

/**
 * Los módulos que carga `index.html`, en su orden, **menos `api.js`**: el
 * cliente HTTP se sustituye por el doble. `app.js` va el último, como allí.
 */
const MODULOS = [
  "config.js",
  "traza.js",
  "cola.js",
  "seleccion.js",
  "pipeline.js",
  "confirmacion.js",
  "autoguardado.js",
];

const HASH = "a1b2c3d4e5f6";
const OTRO_HASH = "f6e5d4c3b2a1";
const OID = "oid-inventado-para-el-test";
const CORREO = "fulanito@ejemplo.invalido";
const INCIDENCIA_GUARDADA = "RS26.08/0123";
const INCIDENCIA_CORREGIDA = "RS26.09/0999";

/** El bloque de estado que devuelve el backend al guardar un parte aprobado. */
const BLOQUE_APROBADO = { estado: "aprobado", decidido_por_persona: false };

/** El veredicto que devuelve `/api/validar` para un parte bueno, inventado. */
const VALIDACION_APTA = { veredicto: "apto", destino: "archivo_directo", motivos: [] };

/** Una promesa que resuelve cuando el test lo diga. */
function diferida() {
  const caja = {};
  caja.promesa = new Promise(function (resolver) {
    caja.resolver = resolver;
  });
  return caja;
}

/** Deja correr las microtareas pendientes, sin tocar el reloj. */
async function respirar() {
  for (let tic = 0; tic < 50; tic += 1) {
    await Promise.resolve();
  }
}

/** Un 409 con la forma exacta que produce `js/api.js::clasificar`. */
function error409(mensaje) {
  const error = new Error(mensaje);
  error.name = "ErrorApi";
  error.tipo = "no_apto";
  error.http = 409;
  error.mensaje = mensaje;
  error.avisos = [];
  return error;
}

/**
 * El front entero, cargado en un contexto aislado y con el doble de la API.
 *
 * @param {Object} [ajustes] Respuestas del doble, por petición:
 *        `{guardarParte, archivar, adjuntar, cerrar}`, cada una
 *        `(cuerpo, hash) => Promise`. Lo que no se diga, responde bien.
 */
function montarFront(ajustes) {
  const opciones = ajustes || {};
  const llamadas = [];
  const temporizadores = [];

  function apuntar(que, cuerpo, hash) {
    llamadas.push({ que: que, cuerpo: cuerpo, hash: hash });
  }

  const apiDoble = {
    validar(cuerpo, hash) {
      apuntar("validar", cuerpo, hash);
      return Promise.resolve(VALIDACION_APTA);
    },
    guardarParte(cuerpo, hash) {
      apuntar("guardar", cuerpo, hash);
      return opciones.guardarParte
        ? opciones.guardarParte(cuerpo, hash)
        : Promise.resolve({ estado: BLOQUE_APROBADO });
    },
    archivar(cuerpo, hash) {
      apuntar("archivar", cuerpo, hash);
      return opciones.archivar
        ? opciones.archivar(cuerpo, hash)
        : Promise.resolve({ nombre_fichero: "inventado.pdf", carpeta: "X", estado: "subido" });
    },
    adjuntar(cuerpo, hash) {
      apuntar("adjuntar", cuerpo, hash);
      return opciones.adjuntar
        ? opciones.adjuntar(cuerpo, hash)
        : Promise.resolve({ estado: "adjuntado", numero_incidencia: INCIDENCIA_GUARDADA });
    },
    cerrar(cuerpo, hash) {
      apuntar("cerrar", cuerpo, hash);
      return opciones.cerrar
        ? opciones.cerrar(cuerpo, hash)
        : Promise.resolve({ estado: "cerrado", numero_incidencia: cuerpo.numero_incidencia });
    },
  };

  const contexto = {
    console: console,
    // El reloj de mentira: apunta y no dispara nunca. El rebote de 1.500 ms
    // del autoguardado se queda aquí dentro para siempre.
    setTimeout(fn, ms) {
      temporizadores.push({ fn: fn, ms: ms });
      return temporizadores.length;
    },
    clearTimeout() {},
    URL: { createObjectURL: () => "blob:inventado", revokeObjectURL: () => {} },
    // El `multipart` del gráfico: basta con que acepte `append`. Lo que lleva
    // dentro lo fija `grafico.test.js`.
    FormData: class FormDataFalso {
      append() {}
    },
  };
  contexto.window = contexto;
  vm.createContext(contexto);

  for (const modulo of MODULOS) {
    const fuente = fs.readFileSync(path.join(RAIZ_JS, modulo), "utf8");
    vm.runInContext(fuente, contexto, { filename: modulo });
  }
  contexto.Api = { crearApi: () => apiDoble };
  vm.runInContext(fs.readFileSync(path.join(RAIZ_JS, "app.js"), "utf8"), contexto, {
    filename: "app.js",
  });

  const app = contexto.appPostventa();
  app.remesaId = "remesa-inventada";
  app.usuario = { usuarioOid: OID, correo: CORREO };

  return {
    app: app,
    window: contexto,
    llamadas: llamadas,
    /** Solo el nombre de cada petición, en orden. */
    orden: () => llamadas.map((una) => una.que),
    /** Las peticiones que escriben en SharePoint o en el ERP. */
    escrituras: () =>
      llamadas.filter((una) => ["archivar", "adjuntar", "cerrar"].includes(una.que)),
  };
}

/** Los nueve campos de un parte, todos inventados. */
function camposInventados() {
  return {
    promocion: { valor: "PROMO-INVENTADA", confianza_pct: 90 },
    codigo_obra: { valor: "0677", confianza_pct: 88 },
    unidad: { valor: "3B", confianza_pct: 70 },
    numero_incidencia: { valor: INCIDENCIA_GUARDADA, confianza_pct: 95 },
    fecha_servicio: { valor: "2026-09-01", confianza_pct: 80 },
    descripcion: { valor: "texto inventado", confianza_pct: 60 },
    dni_cliente: { valor: "00000000T", confianza_pct: 55 },
    observaciones: { valor: "manuscrito inventado", confianza_pct: 30 },
    numero_pagina: { valor: "1", confianza_pct: 99 },
  };
}

/**
 * Un parte en el estado que ofrece «Reintentar el cierre»: archivado, con el
 * gráfico ya dentro del ERP y el cierre fallido (R65 de F-012, R19 de F-025).
 *
 * Se da por guardado por el **mismo camino** que usa la pantalla al procesar
 * (`_anotarGuardado`), para que el autoguardado tenga la foto de lo que consta
 * en la base y sepa qué es «distinto de lo guardado».
 */
function parteParaReintentar(front, hash, cambios) {
  const parte = Object.assign(
    {
      hash: hash || HASH,
      origen: "remesa-inventada.pdf",
      paginas_origen: [1],
      modo_deteccion: "inventado",
      // Un PDF de mentira: solo el gráfico lo necesita, y aquí no se lee.
      fichero: { name: "parte-inventado.pdf" },
      ediciones: {},
      extraccion: { campos: camposInventados() },
      firma: { hay_firma: true },
      validacion: VALIDACION_APTA,
      archivado: true,
      grafico: "adjuntado",
      cerrado: false,
      estado: "adjuntado",
      error: "el ERP no respondió, inventado",
      paso: "",
    },
    cambios || {},
  );
  front.app.partes.push(parte);
  front.app._anotarGuardado(parte, { ok: true, motivo: "", estado: BLOQUE_APROBADO });
  return parte;
}

/** La persona abre el parte y corrige un campo, como en pantalla. */
function corregir(front, parte, nombre, valor) {
  front.app.abrirParte(parte);
  front.app.editarCampo(nombre, valor);
}

// =========================================================================
// R29 · se guarda lo pendiente, y se ESPERA, antes de lanzar el circuito
// =========================================================================

test("f034 R29: reintentar el cierre con una corrección sin guardar la guarda ANTES de cerrar", async () => {
  // El caso de H-2, tal cual: corregir el número de incidencia y pulsar
  // «Reintentar el cierre» dentro del rebote. El reloj no se corre nunca: si
  // hay guardado, lo ha forzado el reintento.
  const front = montarFront();
  front.app.fase = "resumen";
  const parte = parteParaReintentar(front);
  corregir(front, parte, "numero_incidencia", INCIDENCIA_CORREGIDA);
  assert.deepEqual(front.orden(), [], "el rebote aún no ha saltado");

  await front.app.reintentarCierre(parte);

  assert.deepEqual(
    front.orden(),
    ["validar", "guardar", "cerrar"],
    "el cierre salió sin guardar antes la corrección (R29): el backend cotejaría " +
      "un número que no consta en la base",
  );
  // Y lo que se guardó es la corrección, no lo que leyó la IA.
  const guardado = front.llamadas.find((una) => una.que === "guardar");
  assert.equal(guardado.cuerpo.extraccion.campos.numero_incidencia.valor, INCIDENCIA_CORREGIDA);
  // El cierre lleva el mismo número que acaba de quedar guardado: declarado y
  // guardado coinciden, que es lo que coteja el backend desde F-034.
  const cierre = front.llamadas.find((una) => una.que === "cerrar");
  assert.equal(cierre.cuerpo.numero_incidencia, INCIDENCIA_CORREGIDA);
  assert.equal(parte.cerrado, true);
});

test("f034 R29: con el guardado en vuelo, el cierre NO sale hasta que termina", async () => {
  // «Esperar» no es «lanzar y seguir»: sin el `await`, la petición de cierre
  // saldría con la base a medio escribir, que es la misma ventana con otro
  // nombre.
  const enVuelo = diferida();
  const front = montarFront({ guardarParte: () => enVuelo.promesa });
  front.app.fase = "resumen";
  const parte = parteParaReintentar(front);
  corregir(front, parte, "numero_incidencia", INCIDENCIA_CORREGIDA);

  let terminado = false;
  const reintento = front.app.reintentarCierre(parte).then(() => {
    terminado = true;
  });
  await respirar();

  assert.deepEqual(front.orden(), ["validar", "guardar"], "el guardado está en el aire");
  assert.deepEqual(front.escrituras(), [], "el cierre salió con el guardado todavía en vuelo (R29)");
  assert.equal(terminado, false);

  enVuelo.resolver({ estado: BLOQUE_APROBADO });
  await reintento;

  assert.deepEqual(front.orden(), ["validar", "guardar", "cerrar"]);
});

test("f034 R29: se vacía lo pendiente de otro parte también, no solo del que se reintenta", async () => {
  // `vaciarPendientes` es de F-031 y vacía todo; aquí solo se fija que el
  // reintento la usa entera y no una versión recortada al parte pulsado. Un
  // guardado pendiente de otro parte que se quedara en el rebote saltaría
  // después, con la pantalla ya en otra cosa.
  const front = montarFront();
  front.app.fase = "resumen";
  const parte = parteParaReintentar(front, HASH);
  const otro = parteParaReintentar(front, OTRO_HASH);
  corregir(front, otro, "unidad", "4C");

  await front.app.reintentarCierre(parte);

  const guardados = front.llamadas.filter((una) => una.que === "guardar").map((una) => una.hash);
  assert.deepEqual(guardados, [OTRO_HASH]);
  assert.deepEqual(front.escrituras().map((una) => una.hash), [HASH]);
});

// =========================================================================
// R30 · si el vaciado no sale, no se lanza nada y se dice
// =========================================================================

test("f034 R30: si el guardado se cae, no sale ni una escritura y se pinta el aviso de F-031", async () => {
  const front = montarFront({
    guardarParte: () => Promise.reject(error409("la base no responde, inventado")),
  });
  front.app.fase = "resumen";
  front.app.totalTanda = 7;
  front.app.terminados = 7;
  const parte = parteParaReintentar(front);
  corregir(front, parte, "numero_incidencia", INCIDENCIA_CORREGIDA);

  await front.app.reintentarCierre(parte);

  assert.deepEqual(
    front.escrituras(),
    [],
    "con la corrección sin guardar se ha escrito igualmente (R30): el ERP " +
      "recibiría un número que no consta en la base",
  );
  // El aviso es el de `js/autoguardado.js`, el mismo que pinta
  // `confirmarArchivo`, y no uno inventado aquí.
  assert.equal(front.app.avisoArchivo, front.window.Autoguardado.AVISO_SIN_GUARDAR);
  // Y la pantalla se queda como estaba: ni tanda nueva, ni el circuito tocando
  // el parte. Lo que NO se comprueba es `parte.estado`: el intento de guardado
  // revalida y `_anotarVeredicto` (F-026) lo pone en «listo», igual que haría
  // el rebote 1.500 ms después sin que nadie pulsara nada. No es de esta
  // feature; está anotado como hallazgo H-6 en `progress/impl_F-034.md` §8.
  assert.equal(front.app.fase, "resumen");
  assert.equal(front.app.totalTanda, 7);
  assert.equal(front.app.terminados, 7);
  assert.equal(parte.archivado, true);
  assert.equal(parte.grafico, "adjuntado");
  assert.equal(parte.error, "el ERP no respondió, inventado");
  assert.equal(parte.cerrado, false);
  // `.length` y no `deepEqual`: el array nace en el contexto de `vm` y trae otro
  // `Array.prototype`, así que la comparación estricta fallaría aunque esté vacío.
  assert.equal(front.app.resultadosCierre.length, 0);
  // La guarda de la tanda no se quedó cogida: se podrá volver a pulsar.
  assert.equal(front.window.Pipeline.hayTandaEnCurso(), false);
});

test("f034 R30: tras el fallo, el siguiente reintento vuelve a guardar y entonces sí cierra", async () => {
  // Lo pendiente no se da por escrito porque el primer intento fallara: sigue
  // pendiente, y el siguiente reintento lo guarda antes de cerrar.
  let baseCaida = true;
  const front = montarFront({
    guardarParte: () =>
      baseCaida
        ? Promise.reject(error409("la base no responde, inventado"))
        : Promise.resolve({ estado: BLOQUE_APROBADO }),
  });
  front.app.fase = "resumen";
  const parte = parteParaReintentar(front);
  corregir(front, parte, "numero_incidencia", INCIDENCIA_CORREGIDA);

  await front.app.reintentarCierre(parte);
  assert.deepEqual(front.escrituras(), []);
  assert.equal(front.app.avisoArchivo, front.window.Autoguardado.AVISO_SIN_GUARDAR);

  baseCaida = false;
  await front.app.reintentarCierre(parte);

  const orden = front.orden();
  assert.equal(orden[orden.length - 1], "cerrar");
  assert.equal(orden[orden.length - 2], "guardar", "el cierre no fue precedido de su guardado");
  assert.equal(front.escrituras()[0].cuerpo.numero_incidencia, INCIDENCIA_CORREGIDA);
  // Y el aviso del intento anterior se retira, como en `confirmarArchivo`:
  // dejarlo diría «quedan correcciones sin guardar» encima de un cierre hecho.
  assert.equal(front.app.avisoArchivo, "", "el aviso del intento fallido sigue en pantalla");
});

// =========================================================================
// R31 · el cuerpo del cierre no cambia
// =========================================================================

test("f034 R31: el cuerpo del cierre lleva exactamente las mismas claves que antes", async () => {
  // El reintento solo añade una espera delante; lo que viaja lo compone
  // `cuerpoDeCierre` como siempre. Si esto cambiara, el despliegue «backend
  // primero» de `design.md` §9 dejaría de ser seguro.
  const front = montarFront();
  front.app.fase = "resumen";
  const parte = parteParaReintentar(front);

  await front.app.reintentarCierre(parte);

  const cierre = front.escrituras()[0];
  assert.equal(cierre.que, "cerrar");
  assert.deepEqual(Object.keys(cierre.cuerpo).sort(), [
    "commit",
    "confirmado",
    "correo",
    "destino",
    "estado_archivo",
    "hash",
    "numero_incidencia",
    "usuario_oid",
    "veredicto",
  ]);
  assert.equal(cierre.cuerpo.estado_archivo, "archivado");
  assert.equal(cierre.cuerpo.commit, true);
  assert.equal(cierre.cuerpo.confirmado, true);
});

// =========================================================================
// R32 · los 409 nuevos se pintan en el parte, sin tumbar nada
// =========================================================================

test("f034 R32: un 409 del cierre se pinta en el parte y el reintento no revienta", async () => {
  // El motivo es inventado pero tiene la forma del de `CodigosNoCoinciden`:
  // nombra los dos números y dice qué hacer.
  const motivo =
    "el nº de incidencia de la petición («RS26.09/0999») no es el que consta " +
    "guardado para este parte («RS26.08/0123»), así que no se ha cerrado nada";
  const front = montarFront({ cerrar: () => Promise.reject(error409(motivo)) });
  front.app.fase = "resumen";
  const parte = parteParaReintentar(front);

  await front.app.reintentarCierre(parte);

  // El gráfico sigue dentro del ERP: `adjuntado`, con su botón de reintentar,
  // y el motivo del backend tal cual.
  assert.equal(parte.estado, "adjuntado");
  assert.equal(parte.error, motivo);
  assert.equal(parte.cerrado, false);
  assert.equal(front.app.fase, "resumen");
  assert.equal(front.window.Pipeline.hayTandaEnCurso(), false);
});

test("f034 R32: en una tanda, el 409 de un parte no impide que el otro se cierre", async () => {
  // «Sin tumbar la tanda» es el caso de verdad: una tanda de veinte partes no
  // se para porque uno tenga el número corregido y sin guardar en el ERP.
  const motivo =
    "el código de obra de la petición («0626») no es el que consta guardado " +
    "para este parte («0677»), así que no se ha adjuntado nada";
  const front = montarFront({
    adjuntar: (cuerpo, hash) =>
      hash === HASH
        ? Promise.reject(error409(motivo))
        : Promise.resolve({ estado: "adjuntado", numero_incidencia: INCIDENCIA_GUARDADA }),
  });
  const malo = parteParaReintentar(front, HASH, { grafico: "", estado: "archivado", error: "" });
  const bueno = parteParaReintentar(front, OTRO_HASH, { grafico: "", estado: "archivado", error: "" });

  front.app.pedirConfirmacionArchivo();
  await front.app.confirmarArchivo();

  assert.equal(malo.estado, "error_grafico");
  assert.equal(malo.error, motivo);
  assert.equal(malo.cerrado, false);
  assert.equal(bueno.cerrado, true);
  assert.equal(front.app.fase, "resumen");
  assert.deepEqual(
    front.escrituras().map((una) => `${una.que}:${una.hash}`).sort(),
    [`adjuntar:${HASH}`, `adjuntar:${OTRO_HASH}`, `cerrar:${OTRO_HASH}`].sort(),
  );
});

// =========================================================================
// R33 · lo escrito se queda, y sin cambios no se guarda nada
// =========================================================================

test("f034 R33: aunque el guardado falle, lo que la persona escribió sigue ahí", async () => {
  // F-026 R52 y F-031 R21 conservados: el reintento no puede ser la vía por
  // la que se pierde una corrección que no se pudo escribir.
  const front = montarFront({
    guardarParte: () => Promise.reject(error409("la base no responde, inventado")),
  });
  front.app.fase = "resumen";
  const parte = parteParaReintentar(front);
  corregir(front, parte, "numero_incidencia", INCIDENCIA_CORREGIDA);

  await front.app.reintentarCierre(parte);

  assert.deepEqual(parte.ediciones, { numero_incidencia: INCIDENCIA_CORREGIDA });
  assert.equal(parte.extraccion.campos.numero_incidencia.valor, INCIDENCIA_GUARDADA);
});

test("f034 R33: sin nada distinto de lo guardado, el reintento no dispara ningún guardado", async () => {
  // F-031 R22 conservado: reintentar un cierre sin haber corregido nada no
  // puede costar una escritura contra el PostgreSQL compartido.
  const front = montarFront();
  front.app.fase = "resumen";
  const parte = parteParaReintentar(front);

  await front.app.reintentarCierre(parte);

  assert.deepEqual(front.orden(), ["cerrar"]);
  assert.equal(parte.cerrado, true);
});

test("f034 R33: escribir y deshacer antes de reintentar tampoco guarda nada", async () => {
  const front = montarFront();
  front.app.fase = "resumen";
  const parte = parteParaReintentar(front);
  corregir(front, parte, "numero_incidencia", INCIDENCIA_CORREGIDA);
  front.app.editarCampo("numero_incidencia", INCIDENCIA_GUARDADA);

  await front.app.reintentarCierre(parte);

  assert.deepEqual(front.orden(), ["cerrar"]);
});

// =========================================================================
// `design.md` §7.1 · la confirmación de F-025 no se toca
// =========================================================================

test("f034 §7.1: el reintento no consume ni reinicia la confirmación de la tanda", async () => {
  // `reintentarCierre` se apoya en la confirmación ya dada para ese parte; el
  // vaciado va dentro del reintento y no la toca, ni cuando sale bien ni
  // cuando falla.
  for (const guardarParte of [undefined, () => Promise.reject(error409("inventado"))]) {
    const front = montarFront({ guardarParte: guardarParte });
    front.app.fase = "resumen";
    const armada = front.window.Confirmacion.armar(1000);
    front.app.confirmacionArchivo = armada;
    const parte = parteParaReintentar(front);
    corregir(front, parte, "numero_incidencia", INCIDENCIA_CORREGIDA);

    await front.app.reintentarCierre(parte);

    assert.equal(front.app.confirmacionArchivo, armada);
  }
});
