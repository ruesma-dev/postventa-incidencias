// services/postventa-front/tests_js/guarda_salida.test.js
// F-035 · La guarda de salida del circuito (R78-R80; `design.md` §16.15.2,
// §16.15.3 y §16.15.7).
//
// Desde el ajuste del 2026-10-05 todo el front navega en la misma pestaña,
// también desde `partes.html`. Lo que protegía abrir aparte —que una remesa a
// medias no se pierda al salir— lo protege ahora `js/guarda_salida.js`: un
// `beforeunload` que pide confirmación SOLO cuando hay trabajo sin terminar.
//
// Lo que se prueba aquí:
//
//   - R79: cada condición de la tabla de §16.15.2, en positivo y en negativo,
//     y los cuatro casos que NO son trabajo (página recién abierta, ficheros
//     elegidos sin trocear, todo cerrado o rechazado con el detalle cerrado y
//     lo que queda tras «Empezar otra remesa»).
//   - R80: la guarda SOLO LEE. El estado del circuito se le da como un `Proxy`
//     que lanza (y lo apunta) al escribir cualquier propiedad o al llamar a
//     cualquier función suya, a cualquier profundidad; y si no puede leer el
//     estado (sin Alpine, sin `$data`, sin el elemento o porque lanza), no
//     pregunta.
//   - R78: `alSalir` con trabajo llama a `preventDefault` y pone
//     `returnValue`; sin trabajo deja el evento intacto. `instalar` registra
//     un único `beforeunload` y nada más. Y el fichero, cargado como script
//     en una página (con `window`), se instala solo (`vm`, H16-1).
//
// Los dobles de `Pipeline` y `Autoguardado` salen de los módulos REALES
// (`require`), no de copias: si el circuito cambia un literal de estado, el
// test lo ve. Todo sin red, sin DOM real y sin almacenamiento. TODOS los datos
// son inventados.

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const GuardaSalida = require("../js/guarda_salida.js");
const PipelineReal = require("../js/pipeline.js");
const Autoguardado = require("../js/autoguardado.js");

const { hayTrabajoSinTerminar, leerEstado, alSalir, instalar } = GuardaSalida;

// Las tres fases «en marcha» de `js/app.js` (§16.15.2, fila a), escritas
// aquí y NO leídas del módulo: si la guarda olvida una, este test lo ve.
const FASES_EN_MARCHA = ["troceando", "procesando", "archivando_y_cerrando"];

// ── Dobles ───────────────────────────────────────────────────────────────────

/** El `Pipeline` real con `hayTandaEnCurso` fijado (lo demás, tal cual). */
function pipelineCon(tandaEnCurso) {
  return Object.assign({}, PipelineReal, { hayTandaEnCurso: () => tandaEnCurso });
}

const PIPELINE_QUIETO = pipelineCon(false);

/**
 * El estado de `appPostventa()` que mira la guarda, recién abierta la página
 * (los valores iniciales de `js/app.js`). Lleva también dos métodos del
 * componente: la guarda NO puede llamarlos (R80).
 */
function estadoRecienAbierto(cambios) {
  return Object.assign(
    {
      fase: "inactivo",
      seleccion: [],
      partes: [],
      parteAbierto: null,
      estadoAutoguardado: Autoguardado.INACTIVO,
      motivoDeRechazo: "",
      remesaId: "",
      pendientes() {
        return [];
      },
      _autoguardado() {
        return {};
      },
    },
    cambios || {},
  );
}

let contadorPartes = 0;

/** Un parte inventado; `estado` es el de `estadoParte` (o `null`, sin bloque). */
function parte(estado, cerrado) {
  contadorPartes += 1;
  return {
    hash: `hash-inventado-${contadorPartes}`,
    nombre: `parte-inventado-${contadorPartes}.pdf`,
    estado: "listo",
    cerrado: Boolean(cerrado),
    estadoParte: estado === null ? null : { estado: estado },
    ediciones: {},
  };
}

/**
 * El estado envuelto en un `Proxy` de solo lectura, a cualquier profundidad.
 * Escribir, definir o borrar una propiedad, o LLAMAR a cualquier función que
 * se lea de él, lanza y queda apuntado en `violaciones` (la guarda traga sus
 * excepciones, así que el apunte es lo que el test mira).
 */
function soloLectura(objeto, violaciones, ruta) {
  const donde = ruta || "estado";
  const prohibido = (que) => {
    violaciones.push(que);
    throw new Error(`R80: la guarda no puede ${que}`);
  };
  return new Proxy(objeto, {
    get(destino, clave, receptor) {
      const valor = Reflect.get(destino, clave, receptor);
      const nombre = `${donde}.${String(clave)}`;
      if (typeof valor === "function") {
        return function () {
          prohibido(`llamar a ${nombre}()`);
        };
      }
      if (valor !== null && typeof valor === "object") {
        return soloLectura(valor, violaciones, nombre);
      }
      return valor;
    },
    set(_destino, clave) {
      return prohibido(`escribir ${donde}.${String(clave)}`);
    },
    defineProperty(_destino, clave) {
      return prohibido(`definir ${donde}.${String(clave)}`);
    },
    deleteProperty(_destino, clave) {
      return prohibido(`borrar ${donde}.${String(clave)}`);
    },
  });
}

/** `hayTrabajoSinTerminar` sobre el estado envuelto: devuelve [resultado, violaciones]. */
function juzga(estado, pipeline) {
  const violaciones = [];
  const resultado = hayTrabajoSinTerminar(
    soloLectura(estado, violaciones),
    pipeline || PIPELINE_QUIETO,
    Autoguardado,
  );
  return [resultado, violaciones];
}

/** Una ventana y un documento falsos con Alpine que devuelve `estado`. */
function navegador(estado, opciones) {
  const o = opciones || {};
  const registro = { $data: [], selectores: [], escuchas: [], escuchasDocumento: [] };
  const elemento = { nombre: "div-del-circuito" };
  const documento = {
    querySelector(selector) {
      registro.selectores.push(selector);
      return o.sinElemento ? null : elemento;
    },
    addEventListener(tipo) {
      registro.escuchasDocumento.push(tipo);
    },
  };
  const ventana = {
    Pipeline: o.pipeline || PIPELINE_QUIETO,
    Autoguardado: Autoguardado,
    addEventListener(tipo, manejador) {
      registro.escuchas.push({ tipo, manejador });
    },
  };
  if (!o.sinAlpine) {
    ventana.Alpine = o.sinData
      ? {}
      : {
          $data(el) {
            registro.$data.push(el);
            if (o.dataLanza) throw new Error("Alpine.$data ha fallado (inventado)");
            return estado;
          },
        };
  }
  return { ventana, documento, registro, elemento };
}

/** Un evento `beforeunload` falso que cuenta las llamadas a `preventDefault`. */
function eventoDeSalida() {
  const evento = {
    llamadas: 0,
    preventDefault() {
      evento.llamadas += 1;
    },
  };
  return evento;
}

// ── El módulo ────────────────────────────────────────────────────────────────

test("f035 R80: el módulo expone la guarda y su selector, y nada más", () => {
  assert.deepEqual(Object.keys(GuardaSalida).sort(), [
    "FASES_EN_MARCHA",
    "SELECTOR_CIRCUITO",
    "alSalir",
    "hayTrabajoSinTerminar",
    "instalar",
    "leerEstado",
  ]);
  assert.equal(GuardaSalida.SELECTOR_CIRCUITO, '[x-data="appPostventa()"]');
  assert.deepEqual([...GuardaSalida.FASES_EN_MARCHA], FASES_EN_MARCHA);
  assert.ok(Object.isFrozen(GuardaSalida.FASES_EN_MARCHA), "FASES_EN_MARCHA es una constante congelada");
});

// ── R79 (a) · algo en marcha ────────────────────────────────────────────────

for (const fase of FASES_EN_MARCHA) {
  test(`f035 R79 (a): con la fase «${fase}» hay trabajo sin terminar`, () => {
    const [resultado, violaciones] = juzga(estadoRecienAbierto({ fase }));

    assert.equal(resultado, true);
    assert.deepEqual(violaciones, []);
  });
}

test("f035 R79 (a): con una tanda en curso hay trabajo, aunque la fase ya no lo diga", () => {
  const [resultado, violaciones] = juzga(estadoRecienAbierto({ fase: "revision" }), pipelineCon(true));

  assert.equal(resultado, true);
  assert.deepEqual(violaciones, []);
});

test("f035 R79 (a): la tanda la ve en el Pipeline REAL (conGuardaDeTanda) y deja de verla al terminar", async () => {
  const estado = estadoRecienAbierto({ fase: "revision" });
  let soltar;
  const tanda = PipelineReal.conGuardaDeTanda(
    () =>
      new Promise((resolver) => {
        soltar = resolver;
      }),
  );
  try {
    assert.equal(hayTrabajoSinTerminar(estado, PipelineReal, Autoguardado), true);
  } finally {
    soltar();
    await tanda;
  }
  assert.equal(hayTrabajoSinTerminar(estado, PipelineReal, Autoguardado), false);
});

for (const fase of ["inactivo", "seleccionado", "revision", "resumen"]) {
  test(`f035 R79 (a) negativo: la fase «${fase}», sin nada más, no es trabajo sin terminar`, () => {
    const [resultado, violaciones] = juzga(estadoRecienAbierto({ fase }));

    assert.equal(resultado, false);
    assert.deepEqual(violaciones, []);
  });
}

// ── R79 (b) · correcciones sin guardar ──────────────────────────────────────

for (const [nombre, valor] of [
  ["GUARDANDO", Autoguardado.GUARDANDO],
  ["FALLO", Autoguardado.FALLO],
]) {
  test(`f035 R79 (b): con el autoguardado en ${nombre} hay correcciones sin guardar`, () => {
    const [resultado, violaciones] = juzga(
      estadoRecienAbierto({ fase: "revision", estadoAutoguardado: valor }),
    );

    assert.equal(resultado, true);
    assert.deepEqual(violaciones, []);
  });
}

for (const [nombre, valor] of [
  ["GUARDADO", Autoguardado.GUARDADO],
  ["INACTIVO", Autoguardado.INACTIVO],
]) {
  test(`f035 R79 (b) negativo: con el autoguardado en ${nombre} no hay nada sin guardar`, () => {
    const [resultado, violaciones] = juzga(
      estadoRecienAbierto({ fase: "revision", estadoAutoguardado: valor }),
    );

    assert.equal(resultado, false);
    assert.deepEqual(violaciones, []);
  });
}

// ── R79 (c) · partes por terminar ───────────────────────────────────────────

for (const [que, estadoDelParte] of [
  ["sin bloque de estado (leyendo o con error)", null],
  ["sin marca (por decidir)", ""],
  ["pendiente (por corregir)", PipelineReal.ESTADO_PENDIENTE],
  ["aprobado (por archivar y cerrar)", PipelineReal.ESTADO_APROBADO],
]) {
  test(`f035 R79 (c): un parte ${que}, sin cerrar, es trabajo sin terminar`, () => {
    const partes = [parte(PipelineReal.ESTADO_RECHAZADO), parte(estadoDelParte), parte(null, true)];

    const [resultado, violaciones] = juzga(estadoRecienAbierto({ fase: "revision", partes }));

    assert.equal(resultado, true);
    assert.deepEqual(violaciones, []);
  });
}

test("f035 R79 (c) negativo: un parte rechazado sin cerrar no es trabajo (consta en la base)", () => {
  const partes = [parte(PipelineReal.ESTADO_RECHAZADO), parte(PipelineReal.ESTADO_RECHAZADO)];

  const [resultado, violaciones] = juzga(estadoRecienAbierto({ fase: "revision", partes }));

  assert.equal(resultado, false);
  assert.deepEqual(violaciones, []);
});

test("f035 R79 (c) negativo: un parte con el estado «cerrado» del backend no es trabajo", () => {
  const partes = [parte(PipelineReal.ESTADO_CERRADO)];

  const [resultado, violaciones] = juzga(estadoRecienAbierto({ fase: "resumen", partes }));

  assert.equal(resultado, false);
  assert.deepEqual(violaciones, []);
});

test("f035 R79 (c) negativo: un parte cerrado por el circuito (cerrado: true) no es trabajo, sea cual sea su marca", () => {
  const partes = [parte(PipelineReal.ESTADO_APROBADO, true), parte(null, true), parte("", true)];

  const [resultado, violaciones] = juzga(estadoRecienAbierto({ fase: "resumen", partes }));

  assert.equal(resultado, false);
  assert.deepEqual(violaciones, []);
});

// ── R79 (d) · un parte abierto sin cerrar ───────────────────────────────────

test("f035 R79 (d): un parte abierto sin cerrar es trabajo, aunque esté rechazado (motivo o rebote del autoguardado)", () => {
  const rechazado = parte(PipelineReal.ESTADO_RECHAZADO);

  const [resultado, violaciones] = juzga(
    estadoRecienAbierto({ fase: "revision", partes: [rechazado], parteAbierto: rechazado }),
  );

  assert.equal(resultado, true);
  assert.deepEqual(violaciones, []);
});

test("f035 R79 (d) negativo: un parte abierto que ya está cerrado no es trabajo", () => {
  const cerrado = parte(PipelineReal.ESTADO_APROBADO, true);

  const [resultado, violaciones] = juzga(
    estadoRecienAbierto({ fase: "resumen", partes: [cerrado], parteAbierto: cerrado }),
  );

  assert.equal(resultado, false);
  assert.deepEqual(violaciones, []);
});

// ── R79 · lo que NO es trabajo sin terminar ─────────────────────────────────

test("f035 R79 negativo: la página recién abierta no es trabajo", () => {
  const [resultado, violaciones] = juzga(estadoRecienAbierto());

  assert.equal(resultado, false);
  assert.deepEqual(violaciones, []);
});

test("f035 R79 negativo: ficheros elegidos sin trocear (seleccionado) no son trabajo (D-15)", () => {
  const seleccion = [{ name: "remesa-inventada-1.pdf" }, { name: "remesa-inventada-2.pdf" }];

  const [resultado, violaciones] = juzga(estadoRecienAbierto({ fase: "seleccionado", seleccion }));

  assert.equal(resultado, false);
  assert.deepEqual(violaciones, []);
});

test("f035 R79 negativo: una remesa con todo cerrado o rechazado y el detalle cerrado no es trabajo", () => {
  const partes = [
    parte(PipelineReal.ESTADO_APROBADO, true),
    parte(PipelineReal.ESTADO_RECHAZADO),
    parte(PipelineReal.ESTADO_CERRADO),
    parte(PipelineReal.ESTADO_RECHAZADO, true),
  ];

  const [resultado, violaciones] = juzga(
    estadoRecienAbierto({
      fase: "resumen",
      partes,
      parteAbierto: null,
      estadoAutoguardado: Autoguardado.GUARDADO,
      remesaId: "remesa-inventada",
    }),
  );

  assert.equal(resultado, false);
  assert.deepEqual(violaciones, []);
});

test("f035 R79 negativo: lo que queda tras «Empezar otra remesa» (reiniciar) no es trabajo", () => {
  // Los valores que deja `reiniciar()` de `js/app.js`.
  const [resultado, violaciones] = juzga(
    estadoRecienAbierto({
      fase: "inactivo",
      seleccion: [],
      partes: [],
      parteAbierto: null,
      estadoAutoguardado: "",
      motivoDeRechazo: "",
      remesaId: "",
    }),
  );

  assert.equal(resultado, false);
  assert.deepEqual(violaciones, []);
});

// ── R79 · estado ausente o raro: false y nunca lanza ────────────────────────

for (const [que, estado] of [
  ["null", null],
  ["undefined", undefined],
  ["un objeto vacío", {}],
  ["un número", 7],
  ["partes que no es una lista", { fase: "revision", partes: "x" }],
  ["partes con huecos nulos", { fase: "revision", partes: [null, undefined] }],
]) {
  test(`f035 R79: con un estado ${que}, false y sin lanzar`, () => {
    assert.equal(hayTrabajoSinTerminar(estado, PIPELINE_QUIETO, Autoguardado), false);
  });
}

test("f035 R79: si leer el estado lanza, false y sin lanzar", () => {
  const traicionero = {
    get fase() {
      throw new Error("lectura que falla (inventada)");
    },
  };

  assert.equal(hayTrabajoSinTerminar(traicionero, PIPELINE_QUIETO, Autoguardado), false);
});

test("f035 R79: sin Pipeline ni Autoguardado, false y sin lanzar", () => {
  assert.equal(hayTrabajoSinTerminar(estadoRecienAbierto({ fase: "revision" }), undefined, undefined), false);
});

// ── R80 · solo lee ──────────────────────────────────────────────────────────

test("f035 R80: el control del Proxy funciona: escribir o llamar lanza y queda apuntado", () => {
  const violaciones = [];
  const estado = soloLectura(estadoRecienAbierto({ partes: [parte("")] }), violaciones);

  assert.throws(() => {
    estado.fase = "inactivo";
  });
  assert.throws(() => estado.pendientes());
  assert.throws(() => estado._autoguardado());
  assert.throws(() => {
    estado.partes[0].cerrado = true;
  });
  assert.equal(violaciones.length, 4);
});

test("f035 R80: con cada condición a la vez la guarda solo lee (ni escribe ni llama a nada del estado)", () => {
  const abierto = parte(PipelineReal.ESTADO_PENDIENTE);
  const estado = estadoRecienAbierto({
    fase: "procesando",
    partes: [abierto, parte(PipelineReal.ESTADO_RECHAZADO), parte(PipelineReal.ESTADO_APROBADO, true)],
    parteAbierto: abierto,
    estadoAutoguardado: Autoguardado.FALLO,
    motivoDeRechazo: "motivo inventado",
  });

  const [resultado, violaciones] = juzga(estado, pipelineCon(true));

  assert.equal(resultado, true);
  assert.deepEqual(violaciones, []);
});

// ── R80 · leerEstado: Alpine.$data en el momento del evento, o null ─────────

test("f035 R80: leerEstado lee Alpine.$data del elemento del circuito", () => {
  const estado = estadoRecienAbierto();
  const { ventana, documento, registro, elemento } = navegador(estado);

  assert.equal(leerEstado(ventana, documento), estado);
  assert.deepEqual(registro.selectores, ['[x-data="appPostventa()"]']);
  assert.deepEqual(registro.$data, [elemento]);
});

for (const [que, opciones] of [
  ["sin Alpine", { sinAlpine: true }],
  ["con Alpine sin $data", { sinData: true }],
  ["sin el elemento del circuito", { sinElemento: true }],
  ["con un $data que lanza", { dataLanza: true }],
]) {
  test(`f035 R80: leerEstado ${que} devuelve null y no lanza`, () => {
    const { ventana, documento } = navegador(estadoRecienAbierto({ fase: "procesando" }), opciones);

    assert.equal(leerEstado(ventana, documento), null);
  });
}

test("f035 R80: sin el elemento, leerEstado no llama a Alpine.$data", () => {
  const { ventana, documento, registro } = navegador(estadoRecienAbierto(), { sinElemento: true });

  leerEstado(ventana, documento);

  assert.deepEqual(registro.$data, []);
});

test("f035 R80: leerEstado sin ventana ni documento devuelve null y no lanza", () => {
  assert.equal(leerEstado(undefined, undefined), null);
  assert.equal(leerEstado({ Alpine: { $data: () => ({}) } }, null), null);
  const documentoQueLanza = {
    querySelector() {
      throw new Error("selector que falla (inventado)");
    },
  };
  assert.equal(leerEstado({ Alpine: { $data: () => ({}) } }, documentoQueLanza), null);
});

// ── R78 · alSalir: pide confirmación solo con trabajo ───────────────────────

test("f035 R78: con trabajo sin terminar, alSalir llama a preventDefault, pone returnValue y devuelve true", () => {
  const { ventana, documento } = navegador(estadoRecienAbierto({ fase: "troceando" }));
  const evento = eventoDeSalida();

  assert.equal(alSalir(evento, ventana, documento), true);
  assert.equal(evento.llamadas, 1);
  assert.equal(evento.returnValue, true);
});

test("f035 R78: sin trabajo, alSalir deja el evento intacto y devuelve false", () => {
  const { ventana, documento } = navegador(estadoRecienAbierto());
  const evento = eventoDeSalida();

  assert.equal(alSalir(evento, ventana, documento), false);
  assert.equal(evento.llamadas, 0);
  assert.ok(!("returnValue" in evento), "sin trabajo no se toca returnValue");
});

test("f035 R78: alSalir lee la tanda y el autoguardado de la ventana (window.Pipeline, window.Autoguardado)", () => {
  const { ventana, documento } = navegador(estadoRecienAbierto({ fase: "revision" }), {
    pipeline: pipelineCon(true),
  });
  const evento = eventoDeSalida();

  assert.equal(alSalir(evento, ventana, documento), true);
  assert.equal(evento.llamadas, 1);
});

for (const [que, opciones] of [
  ["sin Alpine", { sinAlpine: true }],
  ["con Alpine sin $data", { sinData: true }],
  ["sin el elemento del circuito", { sinElemento: true }],
  ["con un $data que lanza", { dataLanza: true }],
]) {
  test(`f035 R80: ${que}, alSalir no pregunta aunque el estado tuviera trabajo (falla abierta)`, () => {
    const { ventana, documento } = navegador(estadoRecienAbierto({ fase: "procesando" }), opciones);
    const evento = eventoDeSalida();

    assert.equal(alSalir(evento, ventana, documento), false);
    assert.equal(evento.llamadas, 0);
    assert.ok(!("returnValue" in evento));
  });
}

test("f035 R80: alSalir, con el estado como Proxy de solo lectura, no escribe ni llama a nada", () => {
  const violaciones = [];
  const abierto = parte("");
  const estado = soloLectura(
    estadoRecienAbierto({ fase: "revision", partes: [abierto], parteAbierto: abierto }),
    violaciones,
  );
  const { ventana, documento } = navegador(estado);
  const evento = eventoDeSalida();

  assert.equal(alSalir(evento, ventana, documento), true);
  assert.deepEqual(violaciones, []);
});

// ── R78, R80 · instalar: un solo beforeunload ───────────────────────────────

test("f035 R80: instalar registra exactamente un beforeunload en la ventana, y nada en el documento", () => {
  const { ventana, documento, registro } = navegador(estadoRecienAbierto());

  instalar(ventana, documento);

  assert.deepEqual(
    registro.escuchas.map((e) => e.tipo),
    ["beforeunload"],
  );
  assert.deepEqual(registro.escuchasDocumento, []);
  assert.deepEqual(registro.selectores, [], "instalar no lee el estado: lo lee al salir");
  assert.deepEqual(registro.$data, []);
});

test("f035 R78: el beforeunload instalado pregunta con trabajo y calla sin él (lee el estado al salir)", () => {
  const estado = estadoRecienAbierto();
  const { ventana, documento, registro } = navegador(estado);
  instalar(ventana, documento);
  const manejador = registro.escuchas[0].manejador;

  const sinTrabajo = eventoDeSalida();
  manejador(sinTrabajo);
  assert.equal(sinTrabajo.llamadas, 0);

  estado.fase = "procesando";
  const conTrabajo = eventoDeSalida();
  manejador(conTrabajo);
  assert.equal(conTrabajo.llamadas, 1);
  assert.equal(conTrabajo.returnValue, true);
});

// ── R78 · en la página, la guarda se instala sola al cargarse ───────────────
//
// Con `require` no hay `window`, así que la rama del fichero que la conecta al
// navegador (`window.GuardaSalida = …; instalar(window, document);`) no se
// ejecuta en ninguno de los tests de arriba. Aquí se carga el fichero REAL tal
// cual lo carga `partes.html` —como script, en un contexto con `window` y
// `document` y sin `module`— y se mira que quede escuchando (review del
// bloque 16, H16-1).

test("f035 R78: cargada como script en la página, la guarda se instala sola y su beforeunload pregunta con trabajo", () => {
  const ruta = path.join(__dirname, "..", "js", "guarda_salida.js");
  const codigo = fs.readFileSync(ruta, "utf8");
  const estado = estadoRecienAbierto();
  const { ventana, documento, registro } = navegador(estado);

  vm.runInNewContext(codigo, { window: ventana, document: documento }, { filename: ruta });

  assert.deepEqual(
    registro.escuchas.map((e) => e.tipo),
    ["beforeunload"],
    "al cargarse en la página tiene que quedar UN beforeunload registrado",
  );
  assert.deepEqual(registro.escuchasDocumento, []);
  assert.ok(ventana.GuardaSalida, "la guarda queda expuesta como window.GuardaSalida");
  assert.equal(typeof ventana.GuardaSalida.hayTrabajoSinTerminar, "function");

  const manejador = registro.escuchas[0].manejador;

  const sinTrabajo = eventoDeSalida();
  manejador(sinTrabajo);
  assert.equal(sinTrabajo.llamadas, 0, "sin trabajo no pregunta");
  assert.ok(!("returnValue" in sinTrabajo));

  estado.fase = "procesando";
  const conTrabajo = eventoDeSalida();
  manejador(conTrabajo);
  assert.equal(conTrabajo.llamadas, 1, "con trabajo sin terminar pide confirmación");
  assert.equal(conTrabajo.returnValue, true);
});
