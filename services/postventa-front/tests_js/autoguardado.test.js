// services/postventa-front/tests_js/autoguardado.test.js
// F-026 · El autoguardado de las correcciones (R50-R55).
//
// Lo que esta feature viene a arreglar es concreto: hoy `editarCampo` guarda
// la corrección **solo en memoria**, y quien escribe y se va la pierde. Lo que
// se prueba aquí es el mecanismo que lo evita, y las tres cosas que lo hacen
// aceptable:
//
//   1. Una pausa, no una pulsación (R51). Cinco teclas son UN guardado, no
//      cinco, porque al otro lado hay un PostgreSQL **compartido con otros dos
//      proyectos en producción**.
//   2. Si falla, se dice (R52). El aviso **no se va solo** y lo escrito se
//      conserva: quien escribe y no ve nada supone que se guardó.
//   3. Se revalida y se guarda **juntos** (R50), porque guardar sin revalidar
//      deja en la base el veredicto que la IA emitió sobre el dato **sin
//      corregir**.
//
// El módulo no mira el reloj ni conoce el DOM: el temporizador entra por
// parámetro, igual que el instante entra por parámetro en `confirmacion.js`.
// Sin eso, probar «una pausa» costaría segundos de espera real por test.
//
// TODOS los valores están INVENTADOS. Los partes de verdad llevan DNI y
// observaciones manuscritas de clientes y no entran en el repositorio.

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const { crearAutoguardado, GUARDANDO, GUARDADO, FALLO } = require("../js/autoguardado.js");
const Pipeline = require("../js/pipeline.js");

const HASH = "a1b2c3d4e5f6";
const OTRO_HASH = "f6e5d4c3b2a1";
const REMESA = "remesa-inventada-de-test";

const RUTA_CONFIG = path.join(__dirname, "..", "js", "config.js");

/** Evalúa `config.js` igual que lo haría el navegador y devuelve su objeto. */
function cargarConfig() {
  const fuente = fs.readFileSync(RUTA_CONFIG, "utf8");
  const contexto = { window: {} };
  vm.createContext(contexto);
  vm.runInContext(fuente, contexto, { filename: "config.js" });
  return contexto.window.CONFIG_POSTVENTA;
}

/**
 * Un temporizador de mentira: registra lo que se programa y lo que se cancela,
 * y solo dispara cuando el test lo dice.
 *
 * Registrar las cancelaciones no es adorno: la diferencia entre «cinco teclas,
 * un guardado» y «cinco teclas, cinco guardados» es exactamente que cada
 * pulsación **cancele** la anterior, y eso no se ve mirando solo cuántas veces
 * se guardó al final.
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
    /**
     * Dispara los temporizadores vivos, en orden, y espera a que terminen.
     *
     * Da un respiro entre uno y otro —unos cuantos microtareas— porque en el
     * navegador entre dos pausas de 1.500 ms cabe de sobra una petición
     * entera, y sin ese respiro el segundo guardado se encontraría al primero
     * todavía en el aire, que es una carrera del test y no del código.
     *
     * Vuelve a mirar si han aparecido temporizadores nuevos, porque el módulo
     * reprograma cuando se le pide guardar con otro guardado en vuelo. Con un
     * tope, para que un módulo que reprogramara sin fin no colgase la suite.
     */
    async correr() {
      for (let vuelta = 0; vuelta < 10; vuelta += 1) {
        const vivos = reloj.vivos();
        if (vivos.length === 0) {
          return;
        }
        for (const uno of vivos) {
          for (let tic = 0; tic < 10; tic += 1) {
            await Promise.resolve();
          }
          uno.disparado = true;
          await uno.fn();
        }
      }
      throw new Error(
        "el autoguardado sigue programando guardados después de diez vueltas",
      );
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
    firma: { firma: { clasificacion: "ilegible", confianza_pct: 40 } },
    extraccion: {
      campos: {
        promocion: { valor: "PROMO-INVENTADA", confianza_pct: 90 },
        codigo_obra: { valor: "OBRA-0001", confianza_pct: 88 },
        unidad: { valor: "3B", confianza_pct: 70 },
        numero_incidencia: { valor: "12345", confianza_pct: 95 },
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
    retardoMs: opciones.retardoMs === undefined ? 1500 : opciones.retardoMs,
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

// =========================================================================
// R51 · una pausa, no una pulsación
// =========================================================================

test("f026 R51: teclear cinco veces seguidas produce UN guardado, no cinco", async () => {
  const montaje = montar();
  const parte = parteInventado();
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  "12345".split("").forEach(function (_, indice) {
    montaje.auto.alEscribir(parte, "unidad", "3B" + "x".repeat(indice + 1));
  });
  await montaje.reloj.correr();

  assert.deepEqual(montaje.guardados, [HASH]);
  // Y las cuatro primeras se cancelaron: eso es lo que hace que sea una pausa
  // y no cinco escrituras contra una base compartida.
  assert.equal(montaje.reloj.cancelados.length, 4);
});

test("f026 R51: reescribir el mismo valor no produce ningún guardado", async () => {
  const montaje = montar();
  const parte = parteInventado();
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  const resultado = montaje.auto.alEscribir(parte, "unidad", "3B");
  await montaje.reloj.correr();

  assert.equal(resultado.programado, false);
  assert.deepEqual(montaje.guardados, []);
});

test("f026 R51: escribir y deshacer deja la pantalla sin nada que guardar", async () => {
  // El caso real: alguien teclea una letra de más y la borra. Lo que queda es
  // el valor guardado, así que no hay motivo para escribir en la base.
  const montaje = montar();
  const parte = parteInventado();
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  montaje.auto.alEscribir(parte, "unidad", "3BB");
  montaje.auto.alEscribir(parte, "unidad", "3B");
  await montaje.reloj.correr();

  assert.deepEqual(montaje.guardados, []);
  assert.deepEqual(montaje.reloj.vivos(), []);
});

test("f026 R51: los espacios de sobra no son un cambio", () => {
  // `js/pipeline.js::normalizarValor` recorta antes de enviar, así que «3B » y
  // «3B» llegan iguales al backend. Guardar por ese espacio sería una
  // escritura contra la base compartida que no cambia ni un byte.
  const montaje = montar();
  const parte = parteInventado();
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  assert.equal(montaje.auto.alEscribir(parte, "unidad", " 3B ").programado, false);
});

test("f026 R51: un campo que la IA dejó vacío y sigue vacío tampoco es un cambio", () => {
  const montaje = montar();
  const parte = parteInventado();
  parte.extraccion.campos.unidad = { valor: null, confianza_pct: 0 };
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  assert.equal(montaje.auto.alEscribir(parte, "unidad", "").programado, false);
});

test("f026 R51: el retardo es el de config.js y el módulo lo exige", () => {
  const config = cargarConfig();

  assert.equal(typeof config.RETARDO_AUTOGUARDADO_MS, "number");
  assert.ok(config.RETARDO_AUTOGUARDADO_MS > 0);

  // Sin retardo no hay pausa que valga: el módulo se niega a montarse antes
  // que a escribir por tecla contra una base compartida.
  assert.throws(function () {
    crearAutoguardado({ guardar: function () {}, retardoMs: 0 });
  }, /retardo/i);
});

test("f026 R51: el guardado se programa con el retardo que le pasan, sin inventarse otro", () => {
  const montaje = montar({ retardoMs: cargarConfig().RETARDO_AUTOGUARDADO_MS });
  const parte = parteInventado();
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  montaje.auto.alEscribir(parte, "unidad", "4C");

  assert.equal(montaje.reloj.vivos().length, 1);
  assert.equal(montaje.reloj.vivos()[0].ms, cargarConfig().RETARDO_AUTOGUARDADO_MS);
});

test("f026 R51: cambiar de parte con una corrección a medias la guarda, no la tira", async () => {
  // Si la pausa del parte A se cancelara al abrir el parte B, lo escrito en A
  // se perdería en silencio, que es justo el defecto que R50 viene a cerrar.
  const montaje = montar();
  const parteA = parteInventado(HASH);
  const parteB = parteInventado(OTRO_HASH);
  montaje.auto.anotarGuardado(parteA, valoresDe(parteA));
  montaje.auto.anotarGuardado(parteB, valoresDe(parteB));

  montaje.auto.alEscribir(parteA, "unidad", "4C");
  montaje.auto.alEscribir(parteB, "unidad", "5D");
  await montaje.reloj.correr();

  assert.deepEqual(montaje.guardados, [HASH, OTRO_HASH]);
});

// =========================================================================
// R50 · se revalida y se guarda JUNTOS, nunca lo segundo sin lo primero
// =========================================================================

/** Un doble de `js/api.js` que anota, en orden, qué se le pidió. */
function apiDoble(ajustes) {
  const opciones = ajustes || {};
  const llamadas = [];
  return {
    llamadas: llamadas,
    validar(cuerpo) {
      llamadas.push("validar");
      if (opciones.validarFalla) {
        return Promise.reject(new Error("validar falló, inventado"));
      }
      opciones.cuerposValidados && opciones.cuerposValidados.push(cuerpo);
      return Promise.resolve({
        hash_parte: HASH,
        veredicto: "no_apto",
        destino: "revision_manual",
        motivos: [{ codigo: "observaciones_manuscritas", texto: "hay texto a mano" }],
      });
    },
    guardarParte(cuerpo) {
      llamadas.push("parte");
      if (opciones.guardarFalla) {
        return Promise.reject(new Error("guardar falló, inventado"));
      }
      opciones.cuerposGuardados && opciones.cuerposGuardados.push(cuerpo);
      return Promise.resolve({ guardado: true, aprobacion: null });
    },
  };
}

test("f026 R50: el autoguardado revalida y guarda, en ese orden y en el mismo ciclo", async () => {
  // El acoplamiento no es un descuido: guardar sin revalidar dejaría en la
  // base el veredicto que la IA emitió sobre el dato SIN corregir, y las tres
  // puertas de F-026 leen ese veredicto para decidir si el parte circula.
  const api = apiDoble();
  const parte = parteInventado();
  const montaje = montar({
    guardar: function (uno) {
      return Pipeline.revalidarYGuardar(uno, api, REMESA);
    },
  });
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  montaje.auto.alEscribir(parte, "unidad", "4C");
  await montaje.reloj.correr();

  assert.deepEqual(api.llamadas, ["validar", "parte"]);
});

test("f026 R50: nunca se guarda sin haber revalidado antes", async () => {
  // El control que importa: si la revalidación se cae, NO se guarda. Guardar
  // ahí dejaría el dato nuevo con el veredicto viejo, que es exactamente la
  // invariante que R50 mantiene.
  const api = apiDoble({ validarFalla: true });
  const parte = parteInventado();
  const montaje = montar({
    guardar: function (uno) {
      return Pipeline.revalidarYGuardar(uno, api, REMESA);
    },
  });
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  montaje.auto.alEscribir(parte, "unidad", "4C");
  await montaje.reloj.correr();

  assert.deepEqual(api.llamadas, ["validar"]);
  assert.ok(
    !api.llamadas.includes("parte"),
    "se guardó el parte sin veredicto nuevo: en la base quedaría el dato " +
      "corregido con el veredicto del dato sin corregir",
  );
});

test("f026 R50: y cuando la revalidación se cae, el autoguardado lo cuenta como fallo", async () => {
  const api = apiDoble({ validarFalla: true });
  const parte = parteInventado();
  const montaje = montar({
    guardar: function (uno) {
      return Pipeline.revalidarYGuardar(uno, api, REMESA);
    },
  });
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  montaje.auto.alEscribir(parte, "unidad", "4C");
  await montaje.reloj.correr();

  assert.equal(montaje.auto.estado(), FALLO);
});

// =========================================================================
// R52 · los tres estados, y el que importa es el tercero
// =========================================================================

test("f026 R52: el camino feliz publica guardando y luego guardado", async () => {
  const montaje = montar();
  const parte = parteInventado();
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  montaje.auto.alEscribir(parte, "unidad", "4C");
  await montaje.reloj.correr();

  assert.deepEqual(
    montaje.estados.map((uno) => uno.estado),
    [GUARDANDO, GUARDADO],
  );
});

test("f026 R52: si la petición falla, se dice que NO se ha guardado", async () => {
  // Quien escribe y no ve nada supone que se guardó, y esa suposición no
  // puede quedar sin desmentir: es media feature.
  const montaje = montar({
    guardar: function () {
      return Promise.reject(new Error("la base no responde, inventado"));
    },
  });
  const parte = parteInventado();
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  montaje.auto.alEscribir(parte, "unidad", "4C");
  await montaje.reloj.correr();

  assert.equal(montaje.auto.estado(), FALLO);
  assert.match(montaje.auto.mensaje(), /no se ha podido guardar/i);
});

test("f026 R52: el aviso de fallo NO se va solo", async () => {
  // Un aviso que se borra a los tres segundos es un aviso que nadie llega a
  // leer, y el defecto que deja detrás —creer que está guardado lo que no lo
  // está— es peor que no avisar.
  const montaje = montar({
    guardar: function () {
      return Promise.reject(new Error("la base no responde, inventado"));
    },
  });
  const parte = parteInventado();
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  montaje.auto.alEscribir(parte, "unidad", "4C");
  await montaje.reloj.correr();

  // Solo se programó el rebote del guardado. Ningún temporizador más, que es
  // la única forma de que el aviso se borrara solo.
  assert.equal(montaje.reloj.programados.length, 1);
  assert.equal(montaje.auto.estado(), FALLO);
});

test("f026 R52: tras el fallo, lo escrito se conserva y sigue pendiente de guardar", async () => {
  const montaje = montar({
    guardar: function () {
      return Promise.reject(new Error("la base no responde, inventado"));
    },
  });
  const parte = parteInventado();
  parte.ediciones.unidad = "4C";
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  montaje.auto.alEscribir(parte, "unidad", "4C");
  await montaje.reloj.correr();

  // Lo que la persona escribió sigue donde estaba: el módulo no lo toca ni
  // para reintentar ni para rendirse.
  assert.deepEqual(parte.ediciones, { unidad: "4C" });
  // Y sigue constando como no guardado, así que la siguiente pausa lo
  // reintenta en vez de darlo por escrito.
  assert.equal(montaje.auto.hayPendiente(parte), true);
});

test("f026 R52: un guardado correcto después del fallo quita el aviso", async () => {
  let falla = true;
  const montaje = montar({
    guardar: function () {
      if (falla) {
        return Promise.reject(new Error("la base no responde, inventado"));
      }
      return Promise.resolve({});
    },
  });
  const parte = parteInventado();
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  montaje.auto.alEscribir(parte, "unidad", "4C");
  await montaje.reloj.correr();
  assert.equal(montaje.auto.estado(), FALLO);

  falla = false;
  montaje.auto.alEscribir(parte, "unidad", "5D");
  await montaje.reloj.correr();

  assert.equal(montaje.auto.estado(), GUARDADO);
  assert.equal(montaje.auto.hayPendiente(parte), false);
});

// =========================================================================
// R53 · la corrección NO pisa lo que leyó la máquina
// =========================================================================

test("f026 R53: guardar una corrección deja intacto lo que extrajo la IA", async () => {
  // Esto no es higiene: **F-015 lo va a necesitar**. Evaluar el prompt exige
  // comparar lo que dijo el modelo con lo que resultó ser verdad, y un prompt
  // no se puede evaluar contra un dato que una persona corrigió encima. Si el
  // autoguardado pisara `extraccion`, F-015 se quedaría sin evidencia y nadie
  // se enteraría hasta que hiciera falta.
  const cuerposGuardados = [];
  const api = apiDoble({ cuerposGuardados: cuerposGuardados });
  const parte = parteInventado();
  const montaje = montar({
    guardar: function (uno) {
      return Pipeline.revalidarYGuardar(uno, api, REMESA);
    },
  });
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  parte.ediciones.unidad = "4C";
  montaje.auto.alEscribir(parte, "unidad", "4C");
  await montaje.reloj.correr();

  // Lo que leyó el modelo, tal cual: su valor y su confianza.
  assert.deepEqual(parte.extraccion.campos.unidad, {
    valor: "3B",
    confianza_pct: 70,
  });
  // Y lo que se guardó lleva la corrección, marcada como escrita por una
  // persona. Las dos cosas conviven; ninguna tapa a la otra.
  assert.equal(cuerposGuardados.length, 1);
  assert.deepEqual(cuerposGuardados[0].extraccion.campos.unidad, {
    valor: "4C",
    confianza_pct: 100,
    editado: true,
  });
});

test("f026 R53: componer la foto de los valores tampoco toca la extracción", () => {
  const parte = parteInventado();
  parte.ediciones.unidad = "4C";

  const valores = Pipeline.valoresDeCampos(parte);

  assert.equal(valores.unidad, "4C");
  assert.equal(parte.extraccion.campos.unidad.valor, "3B");
  assert.equal(parte.extraccion.campos.unidad.confianza_pct, 70);
});

// =========================================================================
// R54 · la revocación no ocurre a mitad de palabra
// =========================================================================

test("f026 R54: cinco pulsaciones son UNA escritura, así que como mucho una revocación", async () => {
  // La revocación de una aprobación ocurre **en la escritura**: cada
  // `POST /api/parte` ejecuta el `UPDATE` que revoca si la huella del
  // veredicto cambió. Por tanto, contar las escrituras es contar las
  // revocaciones posibles, y por eso una pausa no puede valer cinco.
  const api = apiDoble();
  const parte = parteInventado();
  const montaje = montar({
    guardar: function (uno) {
      return Pipeline.revalidarYGuardar(uno, api, REMESA);
    },
  });
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  "12345".split("").forEach(function (_, indice) {
    montaje.auto.alEscribir(parte, "observaciones", "corrigiendo" + "x".repeat(indice + 1));
  });
  await montaje.reloj.correr();

  const escrituras = api.llamadas.filter(function (una) {
    return una === "parte";
  });
  assert.equal(escrituras.length, 1);
});

test("f026 R54: lo que se revalida es lo escrito hasta la pausa, no una letra suelta", async () => {
  // La huella del veredicto se calcula sobre el dato que se guarda. Si se
  // guardara a mitad de palabra, se revocaría por un veredicto intermedio que
  // nadie quiso: el de media observación.
  const cuerposValidados = [];
  const api = apiDoble({ cuerposValidados: cuerposValidados });
  const parte = parteInventado();
  const montaje = montar({
    guardar: function (uno) {
      return Pipeline.revalidarYGuardar(uno, api, REMESA);
    },
  });
  montaje.auto.anotarGuardado(parte, valoresDe(parte));

  ["c", "cl", "cli", "clie", "client", "cliente"].forEach(function (trozo) {
    parte.ediciones.unidad = trozo;
    montaje.auto.alEscribir(parte, "unidad", trozo);
  });
  await montaje.reloj.correr();

  assert.equal(cuerposValidados.length, 1);
  assert.equal(cuerposValidados[0].extraccion.campos.unidad.valor, "cliente");
});

// =========================================================================
// R55 · aplica a TODOS los partes
// =========================================================================

test("f026 R55: el autoguardado no pregunta por el veredicto: guarda el parte verde igual", async () => {
  // Perder lo escrito es igual de malo en un parte verde. El módulo ni
  // siquiera recibe la validación: no tiene forma de discriminar.
  const montaje = montar();
  const verde = parteInventado();
  verde.validacion = { veredicto: "apto", destino: "archivo_automatico", motivos: [] };
  montaje.auto.anotarGuardado(verde, valoresDe(verde));

  montaje.auto.alEscribir(verde, "unidad", "4C");
  await montaje.reloj.correr();

  assert.deepEqual(montaje.guardados, [HASH]);
});
