// services/postventa-front/tests_js/volcado.test.js
// F-040 R50-R62 · El panel de volcado de `bandeja.html`: lo puro y el componente.
//
// `specs/F-040-volcado-sigrid/design.md` §3.1 (las funciones), §3.2 (qué dice
// el panel al parar) y §3.3 (cómo se monta), contra el contrato
// **implementado** de F-059 (§1) y de F-065 (§1.1): `GET /api/volcado`,
// `POST /api/volcado/ensayo`, `POST /api/volcado/volcar` y
// `GET /api/revision/sigrid`.
//
// Lo que se fija, además de lo obvio:
//
// - «Registrar» sigue su orden (sincronizar → enseñar → ensayar), pide la
//   sincronización UNA vez y para ante cualquier error suyo (R60).
// - Lo que ya existe en Sigrid no se ensaya nunca; lo que choca, solo con su
//   casilla, y viaja en `conflictos_confirmados` con todos sus códigos (R62).
// - El volcado: un solo `confirmado: true`, solo los `previsto`, de uno en
//   uno, y para ante cualquier cosa que no sea un 200 limpio (R52, R53).
// - Ni la `ficha` de Sigrid ni nada de la sincronización sale de la memoria
//   de la página (R55, R61).
//
// Todo inventado: obra 9901, unidades 9901-0N «VILLA 9N», oficio OF01,
// proveedores EJnn, correos @ejemplo.invalid, códigos RS26.10/90NN, UUID con
// ceros que no son de nadie. NI UN TEST ABRE RED: el componente recibe un
// `api` doble y un reloj doble.

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const Volcado = require("../js/volcado.js");
const Revision = require("../js/revision.js");
const Api = require("../js/api.js");
const { recorrer, evaluarEn } = require("./recorrido_html.js");

const OBRA = "9901";
const CORREO = "volcadora@ejemplo.invalid";
const OID = "oid-inventado-para-el-test";
const IDENTIDAD = { usuarioOid: OID, correo: CORREO };

/** Un UUID con ceros: el `n` de `UUID(int=n)`. */
function ID(n) {
  return "00000000-0000-0000-0000-" + String(n).padStart(12, "0");
}

const AHORA = Date.parse("2026-10-31T10:00:00Z");
const CADUCA = "2026-10-31T10:30:00.000000+00:00";
const CADUCA_ANTES = "2026-10-31T10:20:00.000000+00:00";

/** El `catalogo` de `GET /api/revision` (solo lo que usa el panel). La 9901-03 no tiene nombre. */
function catalogo() {
  return {
    unidades: [
      { codigo: "9901-01", nombre: "VILLA 91" },
      { codigo: "9901-02", nombre: "VILLA 92" },
      { codigo: "9901-03", nombre: null },
    ],
    ubicaciones: {},
    oficios: [{ codigo: "OF01", nombre: "FONTANERIA DE EJEMPLO", grupo: null }],
    pares: [{ oficio_codigo: "OF01", proveedor_codigo: "EJ11", proveedor_nombre: "PROVEEDOR EJEMPLO 11" }],
    urgencias: [],
    listados: [],
  };
}

/** Una reclamación de Sigrid con la forma de `_reclamacion` (F-065), con su ficha inventada. */
function reclamacion(cod, estado, unidad, incidenciaId) {
  return {
    cod: cod,
    estado: estado,
    fecha: "2026-10-01",
    unidad_codigo: unidad,
    ubicacion: "COCINA",
    oficio_codigo: "OF01",
    oficio_nombre: "FONTANERIA DE EJEMPLO",
    tipo_codigo: "0002",
    tipo_nombre: "PRIMER LISTADO POSTVENTA",
    descripcion: "Gotea el grifo de ejemplo " + cod,
    referencia: incidenciaId ? "PVI-" + incidenciaId : null,
    incidencia_id: incidenciaId,
    ficha: { propietario: "PERSONA FICTICIA DE LA FICHA", nif: "FICHA-NIF-INVENTADO", telefono: "FICHA-TELEFONO-INVENTADO" },
  };
}

/**
 * El 200 de `GET /api/revision/sigrid?obra=9901` (F-065 §1.1), inventado:
 * ID(1) se enlaza con su parte; ID(2) ya existe; ID(3) choca por criterios;
 * ID(4) choca porque su parte está anulado; ID(5) choca con dos, sin hallazgo
 * que diga por qué; ID(6) y ID(7) van (la 7 en una unidad sin nombre).
 */
function sincronizacion() {
  return {
    obra: OBRA,
    leido_at_utc: "2026-10-31T09:59:00.000000+00:00",
    criterio: { abiertas: ["SAT", "PTE"], cerradas: ["TER", "CER"], umbral_parecido: 50, tope: 5000 },
    reclamaciones: [
      reclamacion("RS26.10/9001", "PTE", "9901-01", ID(1)),
      reclamacion("RS26.10/9002", "SAT", "9901-01", null),
      reclamacion("RS26.10/9003", "SAT", "9901-02", null),
      reclamacion("RS26.10/9004", "NPR", "9901-02", ID(4)),
      reclamacion("RS26.10/9005", "PTE", "9901-02", null),
    ],
    hallazgos: [
      {
        tipo: "coincide",
        severidad: "conflicto",
        incidencia_id: ID(3),
        sigrid_cod: "RS26.10/9003",
        sigrid_cods: ["RS26.10/9003"],
        guardado_cod: null,
        criterios: ["misma_unidad_oficio_ubicacion", "misma_unidad_descripcion_parecida"],
        parecido: 72,
      },
      {
        tipo: "coincide",
        severidad: "conflicto",
        incidencia_id: ID(2),
        sigrid_cod: "RS26.10/9002",
        sigrid_cods: ["RS26.10/9002"],
        guardado_cod: null,
        criterios: ["misma_unidad_oficio_ubicacion", "misma_unidad_descripcion_parecida"],
        parecido: 90,
      },
    ],
    incidencias: {},
    resumen: {},
    volcado: {
      candidatas: 7,
      por_veredicto: { va: 2, se_enlaza: 1, ya_existe: 1, choca: 3 },
      por_unidad: {
        "9901-01": { va: 1, se_enlaza: 1, ya_existe: 1, choca: 0 },
        "9901-02": { va: 0, se_enlaza: 0, ya_existe: 0, choca: 3 },
        "9901-03": { va: 1, se_enlaza: 0, ya_existe: 0, choca: 0 },
      },
      veredictos: [
        { incidencia_id: ID(1), unidad_codigo: "9901-01", estado: "aprobada", veredicto: "se_enlaza", sigrid_cods: ["RS26.10/9001"] },
        { incidencia_id: ID(2), unidad_codigo: "9901-01", estado: "aprobada", veredicto: "ya_existe", sigrid_cods: ["RS26.10/9002"] },
        { incidencia_id: ID(3), unidad_codigo: "9901-02", estado: "aprobada", veredicto: "choca", sigrid_cods: ["RS26.10/9003"] },
        { incidencia_id: ID(4), unidad_codigo: "9901-02", estado: "en_duda", veredicto: "choca", sigrid_cods: ["RS26.10/9004"] },
        { incidencia_id: ID(5), unidad_codigo: "9901-02", estado: "aprobada", veredicto: "choca", sigrid_cods: ["RS26.10/9005", "RS26.10/9003"] },
        { incidencia_id: ID(6), unidad_codigo: "9901-01", estado: "aprobada", veredicto: "va", sigrid_cods: [] },
        { incidencia_id: ID(7), unidad_codigo: "9901-03", estado: "aprobada", veredicto: "va", sigrid_cods: [] },
      ],
    },
  };
}

/** Las candidatas de `GET /api/volcado`: las siete de la sincronización y ID(8), aprobada después. */
function candidatas() {
  return [1, 2, 3, 4, 5, 6, 7, 8].map((n) => ID(n));
}

/** El 200 de `GET /api/volcado?obra=9901` (F-059 §1). */
function panel(partesPorLlamada, ids) {
  const lista = ids || candidatas();
  return {
    obra: OBRA,
    partes_por_llamada: partesPorLlamada === undefined ? 2 : partesPorLlamada,
    resumen: { aprobadas: 7, en_duda: 1, volcadas: 3 },
    candidatas: lista.map((id, i) => ({
      incidencia_id: id,
      revision_id: ID(100 + i),
      estado: id === ID(4) ? "en_duda" : "aprobada",
      ultimo_volcado: null,
    })),
  };
}

/** Un parte del ensayo, con su `envio` (F-059 §1). */
function parte(n, estado, extra) {
  const id = ID(n);
  return Object.assign(
    {
      incidencia_id: id,
      revision_id: ID(200 + n),
      referencia_externa: "PVI-" + id,
      estado: estado,
      motivo: null,
      sigrid_cod: null,
      envio: {
        referencia_externa: "PVI-" + id,
        unidad_postventa: n === 7 ? "9901-03" : n >= 3 && n <= 5 ? "9901-02" : "9901-01",
        descripcion: "Descripción de ejemplo " + n,
        tipo: "0002",
        oficio: "OF01",
        ubicacion: "COCINA",
        forma_comunicacion: "E",
        intervinientes: [{ oficio: "OF01", proveedor: "EJ11", causante: false }],
      },
    },
    extra || {},
  );
}

/** El 200 de `POST /api/volcado/ensayo`. Sin partes, `ensayo_id` y `caduca_at_utc` nulos. */
function ensayo(partes, excluidas, caduca) {
  const lista = partes || [];
  const fuera = excluidas || [];
  const cuantos = (estado) => lista.filter((p) => p.estado === estado).length;
  const conAlgo = lista.length > 0;
  return {
    ensayo_id: conAlgo ? "ensayo-" + lista.map((p) => p.incidencia_id.slice(-2)).join("-") : null,
    obra: OBRA,
    caduca_at_utc: conAlgo ? caduca || CADUCA : null,
    resumen: {
      previstos: cuantos("previsto"),
      idempotentes: cuantos("idempotente"),
      rechazados: cuantos("rechazado"),
      no_procesados: cuantos("no_procesado"),
      excluidas: fuera.length,
    },
    partes: lista,
    excluidas: fuera,
    sigrid: null,
  };
}

/** El 200 de `POST /api/volcado/volcar`. */
function volcado(partes, extra) {
  const lista = partes || [];
  const cuantos = (estado) => lista.filter((p) => p.estado === estado).length;
  return Object.assign(
    {
      llamada_id: lista.length ? "llamada-inventada" : null,
      obra: OBRA,
      resumen: {
        creados: cuantos("creado"),
        idempotentes: cuantos("idempotente"),
        rechazados: cuantos("rechazado"),
        no_procesados: cuantos("no_procesado"),
        sin_respuesta: cuantos("sin_respuesta"),
        excluidas: 0,
      },
      partes: lista,
      excluidas: [],
      avisos: [],
    },
    extra || {},
  );
}

function hecho(n, estado, sigridCod, motivo) {
  return { incidencia_id: ID(n), referencia_externa: "PVI-" + ID(n), estado: estado, motivo: motivo || null, sigrid_cod: sigridCod || null };
}

/** Un `ErrorApi` como el que sale de `js/api.js` ante una respuesta `http` con `cuerpo`. */
function fallo(http, cuerpo) {
  const error = Api.clasificar(http, cuerpo);
  error.http = http;
  if (cuerpo && typeof cuerpo.error === "string") {
    error.mensaje = cuerpo.error;
    error.message = cuerpo.error;
  }
  return error;
}

/** Sin respuesta del servicio: red caída o el corte de los 40 s. */
function corte() {
  return new Api.ErrorApi("transitorio", null, Api.TEXTO_SIN_REINTENTO);
}

// --- R61 · agruparSincronizacion -----------------------------------------------------------

test("f040 R61: agruparSincronizacion reparte los cuatro veredictos en va, ya existe y choca, en el orden de la respuesta", () => {
  const grupos = Volcado.agruparSincronizacion(candidatas(), sincronizacion(), catalogo());

  assert.deepEqual(grupos.va.map((f) => f.incidencia_id), [ID(1), ID(6), ID(7)]);
  assert.deepEqual(grupos.ya_existe.map((f) => f.incidencia_id), [ID(2)]);
  assert.deepEqual(grupos.choca.map((f) => f.incidencia_id), [ID(3), ID(4), ID(5)]);
  assert.deepEqual(
    grupos.orden.map((f) => [f.incidencia_id, f.grupo]),
    [
      [ID(1), "va"],
      [ID(2), "ya_existe"],
      [ID(3), "choca"],
      [ID(4), "choca"],
      [ID(5), "choca"],
      [ID(6), "va"],
      [ID(7), "va"],
    ],
  );
});

test("f040 R61, P-1: se_enlaza va dentro de va, marcada con su código; va a secas no", () => {
  const grupos = Volcado.agruparSincronizacion(candidatas(), sincronizacion(), catalogo());
  const [enlaza, seis] = [grupos.va[0], grupos.va[1]];

  assert.equal(enlaza.veredicto, "se_enlaza");
  assert.equal(enlaza.seEnlaza, true);
  assert.equal(enlaza.enlazaCon, "RS26.10/9001");
  assert.match(enlaza.marca, /se enlaza con RS26\.10\/9001/i);
  assert.equal(seis.seEnlaza, false);
  assert.equal(seis.enlazaCon, null);
  assert.equal(seis.marca, "");
});

test("f040 R61: ya existe lleva sus códigos y sus reclamaciones", () => {
  const grupos = Volcado.agruparSincronizacion(candidatas(), sincronizacion(), catalogo());
  const existe = grupos.ya_existe[0];

  assert.deepEqual(existe.sigrid_cods, ["RS26.10/9002"]);
  assert.deepEqual(existe.reclamaciones.map((r) => [r.cod, r.estado]), [["RS26.10/9002", "SAT"]]);
  assert.equal(existe.incluible, false, "lo que ya existe no se puede incluir");
});

test("f040 R61: el porqué de cada choque: anulada (su emparejada), criterios con su parecido, o nada si no viajó", () => {
  const grupos = Volcado.agruparSincronizacion(candidatas(), sincronizacion(), catalogo());
  const [tres, cuatro, cinco] = grupos.choca;

  assert.deepEqual(tres.reclamaciones.map((r) => r.porque), [
    { tipo: "criterios", criterios: ["misma_unidad_oficio_ubicacion", "misma_unidad_descripcion_parecida"], parecido: 72 },
  ]);
  assert.equal(tres.anulada, false);
  assert.deepEqual(cuatro.reclamaciones.map((r) => r.porque), [{ tipo: "anulada" }]);
  assert.equal(cuatro.anulada, true);
  assert.deepEqual(cinco.reclamaciones.map((r) => [r.cod, r.porque]), [
    ["RS26.10/9005", null],
    ["RS26.10/9003", null],
  ]);
  assert.equal(cinco.anulada, false);
  for (const fila of grupos.choca) {
    assert.equal(fila.incluible, true, `${fila.incidencia_id}: lo que choca se puede incluir con su casilla`);
  }
});

test("f040 R61: cada reclamación citada lleva estado, unidad, ubicación, oficio y descripción", () => {
  const grupos = Volcado.agruparSincronizacion(candidatas(), sincronizacion(), catalogo());
  const r = grupos.choca[0].reclamaciones[0];

  assert.equal(r.cod, "RS26.10/9003");
  assert.equal(r.estado, "SAT");
  assert.equal(r.unidad_codigo, "9901-02");
  assert.equal(r.unidadNombre, "VILLA 92");
  assert.equal(r.ubicacion, "COCINA");
  assert.equal(r.oficio_nombre, "FONTANERIA DE EJEMPLO");
  assert.equal(r.descripcion, "Gotea el grifo de ejemplo RS26.10/9003");
});

test("f040 R61: un código sin reclamación en la respuesta sale igual, con lo que se sabe (su código)", () => {
  const respuesta = sincronizacion();
  respuesta.reclamaciones = respuesta.reclamaciones.filter((r) => r.cod !== "RS26.10/9005");
  const grupos = Volcado.agruparSincronizacion(candidatas(), respuesta, catalogo());

  assert.equal(grupos.choca[2].reclamaciones[0].cod, "RS26.10/9005");
  assert.equal(grupos.choca[2].reclamaciones[0].estado, null);
});

test("f040 R61, R55: la ficha de Sigrid (datos personales) no se guarda en ningún sitio", () => {
  const grupos = Volcado.agruparSincronizacion(candidatas(), sincronizacion(), catalogo());
  const texto = JSON.stringify(grupos);

  assert.doesNotMatch(texto, /ficha/i);
  assert.doesNotMatch(texto, /FICTICIA DE LA FICHA|FICHA-NIF|FICHA-TELEFONO/);
});

test("f040 R61, C-3: el recuento por unidad de cada grupo sale de por_unidad (va = va + se_enlaza), con nombre o código", () => {
  const grupos = Volcado.agruparSincronizacion(candidatas(), sincronizacion(), catalogo());

  assert.deepEqual(grupos.recuento.va, [
    { unidad_codigo: "9901-01", nombre: "VILLA 91", n: 2 },
    { unidad_codigo: "9901-03", nombre: "9901-03", n: 1 },
  ]);
  assert.deepEqual(grupos.recuento.ya_existe, [{ unidad_codigo: "9901-01", nombre: "VILLA 91", n: 1 }]);
  assert.deepEqual(grupos.recuento.choca, [{ unidad_codigo: "9901-02", nombre: "VILLA 92", n: 3 }]);
  assert.deepEqual(grupos.totales, { va: 3, ya_existe: 1, choca: 3 });
});

test("f040 R61: por_unidad manda sobre las filas (es la unidad vigente que cuenta el backend)", () => {
  const respuesta = sincronizacion();
  respuesta.volcado.por_unidad["9901-01"].va = 5;
  const grupos = Volcado.agruparSincronizacion(candidatas(), respuesta, catalogo());

  assert.equal(grupos.recuento.va[0].n, 6);
});

test("f040 R51: sinSincronizar son las candidatas de GET /api/volcado que la sincronización no nombra", () => {
  const grupos = Volcado.agruparSincronizacion(candidatas(), sincronizacion(), catalogo());

  assert.deepEqual(grupos.sinSincronizar, [ID(8)]);
  assert.deepEqual(Volcado.agruparSincronizacion(candidatas().slice(0, 7), sincronizacion(), catalogo()).sinSincronizar, []);
});

test("f040 R61: un veredicto desconocido va a choca SIN casilla (no se puede incluir)", () => {
  const respuesta = sincronizacion();
  respuesta.volcado.veredictos[5].veredicto = "otro_veredicto_futuro";
  const grupos = Volcado.agruparSincronizacion(candidatas(), respuesta, catalogo());
  const raro = grupos.choca.find((f) => f.incidencia_id === ID(6));

  assert.ok(raro, "el desconocido sale en choca");
  assert.equal(raro.incluible, false);
  assert.deepEqual(grupos.va.map((f) => f.incidencia_id), [ID(1), ID(7)]);
  assert.deepEqual(Volcado.paraEnsayar(grupos, { [ID(6)]: true }), [ID(1), ID(7)], "ni con su casilla marcada");
});

test("f040 R61: una respuesta sin bloque volcado no revienta: nada en ningún grupo y todas sin sincronizar", () => {
  const grupos = Volcado.agruparSincronizacion(candidatas(), { obra: OBRA }, catalogo());

  assert.deepEqual([grupos.va, grupos.ya_existe, grupos.choca], [[], [], []]);
  assert.deepEqual(grupos.sinSincronizar, candidatas());
});

// --- R62 · paraEnsayar, confirmadosDelTrozo y el texto del segundo clic ----------------------

test("f040 R62: paraEnsayar lleva lo que va, en el orden de la sincronización, nunca lo que ya existe ni lo no sincronizado", () => {
  const grupos = Volcado.agruparSincronizacion(candidatas(), sincronizacion(), catalogo());

  assert.deepEqual(Volcado.paraEnsayar(grupos, {}), [ID(1), ID(6), ID(7)]);
  assert.deepEqual(
    Volcado.paraEnsayar(grupos, { [ID(2)]: true, [ID(8)]: true }),
    [ID(1), ID(6), ID(7)],
    "ni con la casilla puesta a mano",
  );
});

test("f040 R62, P-2: lo que choca solo entra con SU casilla, por incidencia, en su sitio del orden", () => {
  const grupos = Volcado.agruparSincronizacion(candidatas(), sincronizacion(), catalogo());

  assert.deepEqual(Volcado.paraEnsayar(grupos, { [ID(4)]: true }), [ID(1), ID(4), ID(6), ID(7)]);
  assert.deepEqual(Volcado.paraEnsayar(grupos, { [ID(4)]: false }), [ID(1), ID(6), ID(7)]);
  assert.deepEqual(Volcado.paraEnsayar(grupos, { [ID(4)]: "true" }), [ID(1), ID(6), ID(7)], "solo el booleano true");
  assert.deepEqual(Volcado.paraEnsayar(grupos, [ID(3), ID(5)]), [ID(1), ID(3), ID(5), ID(6), ID(7)], "también una lista");
  assert.deepEqual(Volcado.paraEnsayar(grupos, null), [ID(1), ID(6), ID(7)]);
});

test("f040 R62: confirmadosDelTrozo lleva las incluidas de ESE trozo, con TODOS sus códigos", () => {
  const grupos = Volcado.agruparSincronizacion(candidatas(), sincronizacion(), catalogo());
  const incluidas = { [ID(3)]: true, [ID(5)]: true };

  assert.deepEqual(Volcado.confirmadosDelTrozo([ID(1), ID(5)], grupos, incluidas), [
    { incidencia_id: ID(5), sigrid_cods: ["RS26.10/9005", "RS26.10/9003"] },
  ]);
  assert.deepEqual(Volcado.confirmadosDelTrozo([ID(3), ID(6)], grupos, incluidas), [
    { incidencia_id: ID(3), sigrid_cods: ["RS26.10/9003"] },
  ]);
  assert.deepEqual(Volcado.confirmadosDelTrozo([ID(1), ID(6)], grupos, incluidas), [], "ninguna incluida en el trozo");
  assert.deepEqual(Volcado.confirmadosDelTrozo([ID(4)], grupos, incluidas), [], "una que choca sin su casilla, no");
  assert.deepEqual(Volcado.confirmadosDelTrozo([ID(2)], grupos, { [ID(2)]: true }), [], "lo que ya existe, nunca");
});

test("f040 R62: los códigos confirmados son una copia: tocarlos no cambia la sincronización", () => {
  const grupos = Volcado.agruparSincronizacion(candidatas(), sincronizacion(), catalogo());
  const confirmados = Volcado.confirmadosDelTrozo([ID(3)], grupos, { [ID(3)]: true });
  confirmados[0].sigrid_cods.push("RS26.10/9999");

  assert.deepEqual(grupos.choca[0].sigrid_cods, ["RS26.10/9003"]);
});

test("f040 R62: el texto del segundo clic de una que choca por su parte anulado dice que la enlaza y no crea otro", () => {
  const grupos = Volcado.agruparSincronizacion(candidatas(), sincronizacion(), catalogo());
  const anulada = Volcado.textoInclusion(grupos.choca[1]);
  const normal = Volcado.textoInclusion(grupos.choca[0]);

  assert.match(anulada, /enlaza/i);
  assert.match(anulada, /anulado/i);
  assert.match(anulada, /no crea otro/i);
  assert.match(anulada, /RS26\.10\/9004/);
  assert.doesNotMatch(normal, /enlaza|anulado/i);
  assert.match(normal, /aunque choque/i);
});

test("f040 R61: textoPorque dice por qué choca: su parte anulado, los criterios con su parecido, o que no viajó", () => {
  assert.match(Volcado.textoPorque({ tipo: "anulada" }, { cod: "RS26.10/9004", estado: "NPR" }), /RS26\.10\/9004 está anulado en Sigrid/);
  assert.match(
    Volcado.textoPorque({ tipo: "anulada" }, { cod: "RS26.10/9004", estado: "XYZ" }),
    /RS26\.10\/9004 está en un estado de Sigrid que el panel no conoce \(XYZ\)/,
  );
  const criterios = Volcado.textoPorque(
    { tipo: "criterios", criterios: ["misma_unidad_oficio_ubicacion", "misma_unidad_descripcion_parecida"], parecido: 72 },
    { cod: "RS26.10/9003", estado: "SAT" },
  );
  assert.match(criterios, /misma unidad, oficio y ubicación/);
  assert.match(criterios, /misma unidad y descripción parecida/);
  assert.match(criterios, /72 %/);
  assert.doesNotMatch(
    Volcado.textoPorque({ tipo: "criterios", criterios: ["misma_unidad_oficio_ubicacion"], parecido: null }, { cod: "x" }),
    /%/,
  );
  assert.match(Volcado.textoPorque({ tipo: "criterios", criterios: ["criterio_futuro"], parecido: null }, {}), /criterio_futuro/);
  assert.match(Volcado.textoPorque(null, { cod: "RS26.10/9005" }), /abierta/);
});

// --- R60, R56 · puedeEnsayar --------------------------------------------------------------

test("f040 R60, R56: puedeEnsayar pide sincronización en 200, algo que ensayar y nada en vuelo", () => {
  const grupos = Volcado.agruparSincronizacion(candidatas(), sincronizacion(), catalogo());
  const base = { fase: "sincronizado", grupos: grupos, incluidas: {}, enVuelo: false };

  assert.equal(Volcado.puedeEnsayar(base), true);
  assert.equal(Volcado.puedeEnsayar(Object.assign({}, base, { grupos: null })), false, "sin sincronización");
  assert.equal(Volcado.puedeEnsayar(Object.assign({}, base, { enVuelo: true })), false, "con una petición en vuelo");
  assert.equal(Volcado.puedeEnsayar(Object.assign({}, base, { fase: "parado" })), false, "con la sincronización parada");
  assert.equal(Volcado.puedeEnsayar(Object.assign({}, base, { fase: "ensayado" })), false, "ya ensayado: se vuelve a registrar");
  const soloChoca = Volcado.agruparSincronizacion([ID(3)], {
    volcado: { por_unidad: {}, veredictos: [sincronizacion().volcado.veredictos[2]] },
    reclamaciones: [],
    hallazgos: [],
  }, catalogo());
  assert.equal(Volcado.puedeEnsayar(Object.assign({}, base, { grupos: soloChoca })), false, "nada que ensayar");
  assert.equal(Volcado.puedeEnsayar(Object.assign({}, base, { grupos: soloChoca, incluidas: { [ID(3)]: true } })), true, "con su casilla");
  assert.equal(Volcado.puedeEnsayar(null), false);
});

// --- R51, R52, C-3 · recuentoPorUnidad y trocear ------------------------------------------

test("f040 R51, R52: recuentoPorUnidad cuenta por unidad en el orden de aparición, con el nombre del catálogo o el código", () => {
  const filas = [{ unidad_codigo: "9901-01" }, { unidad_codigo: "9901-03" }, { unidad_codigo: "9901-01" }, { unidad_codigo: "9901-09" }];

  assert.deepEqual(Volcado.recuentoPorUnidad(filas, catalogo()), [
    { unidad_codigo: "9901-01", nombre: "VILLA 91", n: 2 },
    { unidad_codigo: "9901-03", nombre: "9901-03", n: 1 },
    { unidad_codigo: "9901-09", nombre: "9901-09", n: 1 },
  ]);
  assert.deepEqual(Volcado.recuentoPorUnidad([], catalogo()), []);
  assert.deepEqual(Volcado.recuentoPorUnidad(filas.slice(0, 1), null), [{ unidad_codigo: "9901-01", nombre: "9901-01", n: 1 }]);
});

test("f040 R51: trocear parte en grupos de n, en orden, sin perder ni repetir", () => {
  const ids = [1, 2, 3, 4, 5, 6, 7].map(ID);

  assert.deepEqual(Volcado.trocear(ids, 1), ids.map((id) => [id]));
  assert.deepEqual(Volcado.trocear(ids, 5), [ids.slice(0, 5), ids.slice(5)]);
  assert.deepEqual(Volcado.trocear(ids, 3), [ids.slice(0, 3), ids.slice(3, 6), ids.slice(6)]);
  assert.deepEqual(Volcado.trocear(ids, 50), [ids]);
  assert.deepEqual(Volcado.trocear([], 5), []);
});

test("f040 R51: 285 incidencias entre 5 son 57 trozos de 5, sin perder ni repetir ninguna", () => {
  const ids = Array.from({ length: 285 }, (_, i) => ID(i + 1));
  const trozos = Volcado.trocear(ids, 5);

  assert.equal(trozos.length, 57);
  assert.ok(trozos.every((t) => t.length === 5));
  assert.deepEqual(trozos.flat(), ids);
});

test("f040 R51: trocear con un n que no es un entero positivo lanza (nunca un bucle sin fin)", () => {
  for (const n of [0, -1, null, undefined, "5", NaN, 2.5]) {
    assert.throws(() => Volcado.trocear([ID(1)], n), RangeError, String(n));
  }
});

// --- R51, R62 · cuerpoDeEnsayo y excluidasDeLaGuarda ----------------------------------------

test("f040 R51, R62: cuerpoDeEnsayo es exactamente el de F-059, sin confirmado, y conflictos_confirmados solo si hay", () => {
  const sin = Volcado.cuerpoDeEnsayo(OBRA, [ID(1), ID(6)], IDENTIDAD, []);
  assert.deepEqual(sin, { obra: OBRA, usuario_oid: OID, usuario_correo: CORREO, incidencias: [ID(1), ID(6)] });
  assert.deepEqual(Object.keys(sin), ["obra", "usuario_oid", "usuario_correo", "incidencias"]);
  assert.deepEqual(Volcado.cuerpoDeEnsayo(OBRA, [ID(1)], IDENTIDAD, undefined), {
    obra: OBRA,
    usuario_oid: OID,
    usuario_correo: CORREO,
    incidencias: [ID(1)],
  });

  const confirmados = [{ incidencia_id: ID(5), sigrid_cods: ["RS26.10/9005", "RS26.10/9003"] }];
  const con = Volcado.cuerpoDeEnsayo(OBRA, [ID(5)], IDENTIDAD, confirmados);
  assert.deepEqual(con.conflictos_confirmados, confirmados);
  assert.equal("confirmado" in con, false);
  assert.equal("confirmado" in sin, false);
});

test("f040 R51: cuerpoDeEnsayo copia la lista: el trozo no cambia si se toca el cuerpo", () => {
  const trozo = [ID(1)];
  const cuerpo = Volcado.cuerpoDeEnsayo(OBRA, trozo, IDENTIDAD, []);
  cuerpo.incidencias.push(ID(2));

  assert.deepEqual(trozo, [ID(1)]);
});

test("f040 R62: excluidasDeLaGuarda junta duplicada_en_sigrid y conflicto_sin_confirmar y marca lo que cambió desde la sincronización", () => {
  const grupos = Volcado.agruparSincronizacion(candidatas(), sincronizacion(), catalogo());
  const respuestas = [
    ensayo([parte(1, "idempotente")], [
      { incidencia_id: ID(6), motivo: "duplicada_en_sigrid", sigrid_cod: "RS26.10/9010" },
      { incidencia_id: ID(9), motivo: "ya_volcada", sigrid_cod: null },
    ]),
    ensayo([], [
      { incidencia_id: ID(5), motivo: "conflicto_sin_confirmar", sigrid_cod: "RS26.10/9011" },
      { incidencia_id: ID(3), motivo: "conflicto_sin_confirmar", sigrid_cod: "RS26.10/9003" },
      { incidencia_id: ID(4), motivo: "duplicada_en_sigrid", sigrid_cod: "RS26.10/9004" },
    ]),
  ];

  const guarda = Volcado.excluidasDeLaGuarda(respuestas, grupos);

  assert.deepEqual(
    guarda.excluidas.map((e) => [e.incidencia_id, e.motivo, e.sigrid_cod, e.cambio]),
    [
      [ID(6), "duplicada_en_sigrid", "RS26.10/9010", true],
      [ID(5), "conflicto_sin_confirmar", "RS26.10/9011", true],
      [ID(3), "conflicto_sin_confirmar", "RS26.10/9003", false],
      [ID(4), "duplicada_en_sigrid", "RS26.10/9004", false],
    ],
  );
  assert.equal(guarda.hayCambios, true);
  assert.match(guarda.excluidas[0].texto, /Ya existe en Sigrid/);
});

test("f040 R62: excluidasDeLaGuarda sin nada de la guarda: lista vacía y sin cambios; sin grupos, nada marcado", () => {
  const grupos = Volcado.agruparSincronizacion(candidatas(), sincronizacion(), catalogo());

  assert.deepEqual(Volcado.excluidasDeLaGuarda([ensayo([parte(1, "previsto")])], grupos), { excluidas: [], hayCambios: false });
  assert.deepEqual(Volcado.excluidasDeLaGuarda([], grupos), { excluidas: [], hayCambios: false });
  const sinGrupos = Volcado.excluidasDeLaGuarda(
    [ensayo([], [{ incidencia_id: ID(9), motivo: "duplicada_en_sigrid", sigrid_cod: "RS26.10/9012" }])],
    null,
  );
  assert.equal(sinGrupos.excluidas.length, 1);
  assert.equal(sinGrupos.hayCambios, false, "una que no estaba en la sincronización no se marca");
});

// --- R52 · cuerpoDeVolcado -------------------------------------------------------------------

test("f040 R52: cuerpoDeVolcado lleva confirmado true, el ensayo_id y SOLO los previsto, con su revision_id", () => {
  const datos = ensayo([parte(1, "previsto"), parte(6, "idempotente"), parte(7, "previsto"), parte(3, "rechazado", { motivo: "tipo_no_valido" })]);
  const cuerpo = Volcado.cuerpoDeVolcado(datos, IDENTIDAD);

  assert.deepEqual(cuerpo, {
    obra: OBRA,
    ensayo_id: datos.ensayo_id,
    usuario_oid: OID,
    usuario_correo: CORREO,
    confirmado: true,
    incidencias: [
      { incidencia_id: ID(1), revision_id: ID(201) },
      { incidencia_id: ID(7), revision_id: ID(207) },
    ],
  });
  assert.equal(cuerpo.confirmado, true, "el booleano, no la cadena");
  assert.deepEqual(Object.keys(cuerpo), ["obra", "ensayo_id", "usuario_oid", "usuario_correo", "confirmado", "incidencias"]);
});

test("f040 R52: cuerpoDeVolcado sin ningún previsto (o sin ensayo_id) es null: ese trozo no se manda", () => {
  assert.equal(Volcado.cuerpoDeVolcado(ensayo([parte(1, "idempotente"), parte(3, "rechazado")]), IDENTIDAD), null);
  assert.equal(Volcado.cuerpoDeVolcado(ensayo([]), IDENTIDAD), null);
  const sinId = ensayo([parte(1, "previsto")]);
  sinId.ensayo_id = null;
  assert.equal(Volcado.cuerpoDeVolcado(sinId, IDENTIDAD), null);
  assert.equal(Volcado.cuerpoDeVolcado(null, IDENTIDAD), null);
});

// --- R51, R52, R53.5 · juntarEnsayos -----------------------------------------------------------

test("f040 R51: juntarEnsayos hace una tabla con los nombres del catálogo, el tipo y la etiqueta de cada estado", () => {
  const vista = Volcado.juntarEnsayos(
    [
      ensayo([parte(1, "previsto"), parte(6, "idempotente", { sigrid_cod: "RS26.10/9020" })]),
      ensayo([parte(7, "rechazado", { motivo: "tipo_no_valido" }), parte(3, "no_procesado", { motivo: "presupuesto_de_tiempo_agotado" })]),
    ],
    catalogo(),
  );

  assert.deepEqual(
    vista.filas.map((f) => [f.incidencia_id, f.unidad, f.oficio, f.proveedor, f.ubicacion, f.tipo, f.etiqueta]),
    [
      [ID(1), "VILLA 91", "FONTANERIA DE EJEMPLO", "PROVEEDOR EJEMPLO 11", "COCINA", "0002 PRIMER LISTADO POSTVENTA", "Se crearía"],
      [ID(6), "VILLA 91", "FONTANERIA DE EJEMPLO", "PROVEEDOR EJEMPLO 11", "COCINA", "0002 PRIMER LISTADO POSTVENTA", "Ya estaba creado"],
      [ID(7), "9901-03", "FONTANERIA DE EJEMPLO", "PROVEEDOR EJEMPLO 11", "COCINA", "0002 PRIMER LISTADO POSTVENTA", "No se crea"],
      [ID(3), "VILLA 92", "FONTANERIA DE EJEMPLO", "PROVEEDOR EJEMPLO 11", "COCINA", "0002 PRIMER LISTADO POSTVENTA", "No se llegó a intentar"],
    ],
  );
  assert.equal(vista.filas[0].descripcion, "Descripción de ejemplo 1");
  assert.equal(vista.filas[0].motivo, "");
  assert.equal(vista.filas[2].motivo, Revision.textoMotivoVolcado("tipo_no_valido"), "§8.9 por textoMotivoVolcado");
  assert.equal(vista.filas[3].motivo, Revision.textoMotivoVolcado("presupuesto_de_tiempo_agotado"));
});

test("f040 R51: sin nombre en el catálogo, el código del envio (oficio, proveedor); sin envio, guiones", () => {
  const raro = parte(1, "previsto");
  raro.envio.oficio = "OF99";
  raro.envio.intervinientes = [{ oficio: "OF99", proveedor: "EJ99", causante: false }];
  raro.envio.tipo = "0003";
  const sinEnvio = parte(6, "rechazado", { envio: null, motivo: "unidad_postventa_no_encontrada" });
  const vista = Volcado.juntarEnsayos([ensayo([raro, sinEnvio])], catalogo());

  assert.deepEqual([vista.filas[0].oficio, vista.filas[0].proveedor, vista.filas[0].tipo], ["OF99", "EJ99", "0003"]);
  assert.deepEqual(
    [vista.filas[1].unidad, vista.filas[1].oficio, vista.filas[1].proveedor, vista.filas[1].ubicacion, vista.filas[1].descripcion],
    ["—", "—", "—", "—", "—"],
  );
  const conCatalogoVacio = Volcado.juntarEnsayos([ensayo([parte(1, "previsto")])], null);
  assert.deepEqual([conCatalogoVacio.filas[0].unidad, conCatalogoVacio.filas[0].proveedor], ["9901-01", "EJ11"]);
});

test("f040 R51: el proveedor sale del par de SU oficio: el mismo proveedor en otro oficio no vale", () => {
  const otro = parte(1, "previsto");
  otro.envio.oficio = "OF02";
  otro.envio.intervinientes = [{ oficio: "OF02", proveedor: "EJ11", causante: false }];
  const vista = Volcado.juntarEnsayos([ensayo([otro])], catalogo());

  assert.equal(vista.filas[0].proveedor, "EJ11");
});

test("f040 R51, R52: juntarEnsayos cuenta N previstos, las excluidas con su texto y el recuento por unidad de lo que se crearía", () => {
  const vista = Volcado.juntarEnsayos(
    [
      ensayo([parte(1, "previsto"), parte(6, "previsto")], [{ incidencia_id: ID(2), motivo: "duplicada_en_sigrid", sigrid_cod: "RS26.10/9002" }]),
      ensayo([parte(7, "previsto"), parte(3, "rechazado", { motivo: "tipo_no_valido" })]),
    ],
    catalogo(),
  );

  assert.equal(vista.n, 3);
  assert.deepEqual(vista.porUnidad, [
    { unidad_codigo: "9901-01", nombre: "VILLA 91", n: 2 },
    { unidad_codigo: "9901-03", nombre: "9901-03", n: 1 },
  ]);
  assert.deepEqual(vista.excluidas.map((e) => [e.incidencia_id, e.sigrid_cod]), [[ID(2), "RS26.10/9002"]]);
  assert.equal(vista.excluidas[0].texto, Volcado.textoExclusion("duplicada_en_sigrid"));
  assert.deepEqual(vista.resumen, { previstos: 3, idempotentes: 0, rechazados: 1, no_procesados: 0, excluidas: 1 });
  assert.equal(vista.hayIdempotente, false);
});

test("f040 R51: un ensayo 200 sin ensayo_id es un trozo sin previstos, no un fallo; la caducidad es la más temprana de los que tienen", () => {
  const vista = Volcado.juntarEnsayos(
    [
      ensayo([parte(1, "previsto")], [], CADUCA),
      ensayo([], [{ incidencia_id: ID(2), motivo: "duplicada_en_sigrid", sigrid_cod: "RS26.10/9002" }]),
      ensayo([parte(6, "idempotente")], [], CADUCA_ANTES),
    ],
    catalogo(),
  );

  assert.equal(vista.n, 1);
  assert.equal(vista.caduca, CADUCA_ANTES);
  assert.equal(vista.hayIdempotente, true);
  assert.equal(Volcado.juntarEnsayos([ensayo([])], catalogo()).caduca, null);
  assert.equal(Volcado.juntarEnsayos([], catalogo()).n, 0);
});

// --- R52, R56 · puedeVolcar, confirmacionValida, caducado --------------------------------------

function estadoEnsayado(extra) {
  return Object.assign(
    {
      enVuelo: false,
      ensayos: [
        { ok: true, ids: [ID(1), ID(6)], datos: ensayo([parte(1, "previsto"), parte(6, "previsto")]) },
        { ok: true, ids: [ID(7)], datos: ensayo([parte(7, "idempotente")]) },
      ],
    },
    extra || {},
  );
}

test("f040 R52, R56: puedeVolcar con previstos, todos los ensayos en 200, sin caducar y sin nada en vuelo", () => {
  assert.equal(Volcado.puedeVolcar(estadoEnsayado(), AHORA), true);
  assert.equal(Volcado.puedeVolcar(estadoEnsayado({ enVuelo: true }), AHORA), false, "petición en vuelo");
  assert.equal(Volcado.puedeVolcar(estadoEnsayado(), Date.parse(CADUCA)), false, "caducado justo en su instante");
  assert.equal(Volcado.puedeVolcar(estadoEnsayado(), Date.parse(CADUCA) - 1), true, "un milisegundo antes, aún vale");
  const conFallo = estadoEnsayado();
  conFallo.ensayos.push({ ok: false, ids: [ID(3)], error: fallo(502, { error: "x", codigo: "ensayo_sin_respuesta" }) });
  assert.equal(Volcado.puedeVolcar(conFallo, AHORA), false, "un ensayo no-200");
  const sinPrevistos = estadoEnsayado({ ensayos: [{ ok: true, ids: [ID(7)], datos: ensayo([parte(7, "idempotente")]) }] });
  assert.equal(Volcado.puedeVolcar(sinPrevistos, AHORA), false, "sin previstos");
  assert.equal(Volcado.puedeVolcar(estadoEnsayado({ ensayos: [] }), AHORA), false, "sin ensayos");
  assert.equal(Volcado.puedeVolcar(null, AHORA), false);
});

test("f040 R52: puedeVolcar mira la caducidad MÁS TEMPRANA, no la del primero", () => {
  const estado = estadoEnsayado();
  estado.ensayos[1].datos = ensayo([parte(7, "previsto")], [], CADUCA_ANTES);

  assert.equal(Volcado.puedeVolcar(estado, Date.parse(CADUCA_ANTES) + 1000), false);
  assert.equal(Volcado.puedeVolcar(estado, Date.parse(CADUCA_ANTES) - 1000), true);
});

test("f040 R52, D-12: confirmacionValida solo con el número exacto de partes", () => {
  assert.equal(Volcado.confirmacionValida("3", 3), true);
  assert.equal(Volcado.confirmacionValida(" 3 ", 3), true, "los espacios de los lados no cuentan");
  for (const malo of ["2", "4", "", "tres", "3.0", "03", "3a", null, undefined]) {
    assert.equal(Volcado.confirmacionValida(malo, 3), false, String(malo));
  }
  assert.equal(Volcado.confirmacionValida("0", 0), false, "cero partes no se confirman");
  assert.equal(Volcado.confirmacionValida(3, 3), true, "un número tecleado vale igual");
});

test("f040 R52, C-3: el texto de la confirmación dice N, la obra y el recuento por unidad", () => {
  const texto = Volcado.textoConfirmacion(285, [
    { unidad_codigo: "9901-15", nombre: "VILLA 15", n: 280 },
    { unidad_codigo: "9901-14", nombre: "VILLA 14", n: 5 },
  ], OBRA);

  assert.equal(
    texto,
    "Se van a crear 285 partes en el ERP de producción de la obra 9901: 280 de VILLA 15 y 5 de VILLA 14. Escribe 285 para confirmar.",
  );
  assert.equal(
    Volcado.textoConfirmacion(1, [{ unidad_codigo: "9901-01", nombre: "VILLA 91", n: 1 }], OBRA),
    "Se va a crear 1 parte en el ERP de producción de la obra 9901: 1 de VILLA 91. Escribe 1 para confirmar.",
  );
  assert.match(
    Volcado.textoConfirmacion(4, [
      { unidad_codigo: "a", nombre: "A", n: 1 },
      { unidad_codigo: "b", nombre: "B", n: 2 },
      { unidad_codigo: "c", nombre: "C", n: 1 },
    ], OBRA),
    /: 1 de A, 2 de B y 1 de C\./,
  );
});

test("f040 R53.1: caducado mira el caduca_at_utc del ensayo de ese trozo", () => {
  const datos = ensayo([parte(1, "previsto")], [], CADUCA);

  assert.equal(Volcado.caducado(datos, AHORA), false);
  assert.equal(Volcado.caducado(datos, Date.parse(CADUCA)), true);
  assert.equal(Volcado.caducado(datos, Date.parse(CADUCA) - 1), false);
  assert.equal(Volcado.caducado(datos, new Date(Date.parse(CADUCA) + 1)), true, "también con un Date");
  const ilegible = ensayo([parte(1, "previsto")], [], "no-es-una-fecha");
  assert.equal(Volcado.caducado(ilegible, AHORA), true, "una caducidad ilegible no se da por buena");
  assert.equal(Volcado.caducado(ensayo([]), AHORA), true, "sin caducidad no hay nada que mandar");
});

test("f040 R52: la cuenta atrás hasta la caducidad más temprana, en minutos y segundos", () => {
  assert.equal(Volcado.cuentaAtras(CADUCA, AHORA), "30:00");
  assert.equal(Volcado.cuentaAtras(CADUCA, Date.parse(CADUCA) - 61500), "1:01");
  assert.equal(Volcado.cuentaAtras(CADUCA, Date.parse(CADUCA) - 5000), "0:05");
  assert.equal(Volcado.cuentaAtras(CADUCA, Date.parse(CADUCA)), "caducado");
  assert.equal(Volcado.cuentaAtras(null, AHORA), "");
});

// --- R51, R53 · siguientePaso y los textos de cada parada (§3.2) --------------------------------

test("f040 R51, R53: siguientePaso sigue con un 200 limpio y para con cualquier otra cosa", () => {
  assert.equal(Volcado.siguientePaso({ fase: "ensayo", datos: ensayo([parte(1, "previsto")]) }).seguir, true);
  assert.equal(Volcado.siguientePaso({ fase: "volcado", datos: volcado([hecho(1, "creado", "RS26.10/9030")]) }).seguir, true);
  assert.equal(Volcado.siguientePaso({ fase: "sincronizacion", datos: sincronizacion() }).seguir, true);
  for (const fase of ["sincronizacion", "ensayo", "volcado"]) {
    for (const error of [
      fallo(400, { error: "x", codigo: "peticion_invalida" }),
      fallo(409, { error: "x", codigo: "obra_ambigua" }),
      fallo(500, { error: "x", codigo: "volcado_sin_traza" }),
      fallo(502, { error: "x", codigo: "ensayo_sin_respuesta" }),
      fallo(503, { error: "x" }),
      fallo(504, { error: "x" }),
      corte(),
    ]) {
      const paso = Volcado.siguientePaso({ fase: fase, error: error });
      assert.equal(paso.seguir, false, `${fase} ${error.http} ${error.codigo}`);
      assert.ok(paso.mensaje.length > 0, `${fase} ${error.http}: dice por qué`);
    }
  }
});

test("f040 R53.2: un volcado 200 con algún sin_respuesta para y lo dice en duda", () => {
  const paso = Volcado.siguientePaso({
    fase: "volcado",
    datos: volcado([hecho(1, "creado", "RS26.10/9030"), hecho(6, "sin_respuesta")]),
  });

  assert.equal(paso.seguir, false);
  assert.match(paso.mensaje, /en duda/);
  assert.match(paso.mensaje, /no duplica/);
  assert.equal(Volcado.siguientePaso({ fase: "ensayo", datos: { resumen: { sin_respuesta: 3 } } }).seguir, true, "eso es solo del volcado");
});

test("f040 R60, §3.2: la sincronización para y lo dice según el error (también el 503 sin código)", () => {
  const texto = (error) => Volcado.siguientePaso({ fase: "sincronizacion", error: error }).mensaje;

  assert.match(texto(fallo(400, { error: "x", codigo: "peticion_invalida" })), /recarga/i);
  assert.match(texto(fallo(409, { error: "x", codigo: "bandeja_demasiado_grande", total: 12345 })), /12345/);
  assert.match(texto(fallo(409, { error: "x", codigo: "reclamaciones_sin_verificar", filas: 5001 })), /5001/);
  assert.match(texto(fallo(409, { error: "x", codigo: "reclamaciones_sin_verificar", filas: 5001 })), /sistemas/);
  assert.match(texto(fallo(409, { error: "x", codigo: "obra_ambigua" })), /más de una obra/);
  const sinCodigo = texto(fallo(503, { error: "No se ha podido leer Sigrid ahora mismo, inventado." }));
  assert.match(sinCodigo, /No se ha podido leer Sigrid ahora mismo, inventado\./, "el texto del servicio");
  assert.match(sinCodigo, /volver a registrar más tarde/i);
  assert.doesNotMatch(sinCodigo, /entorno no archiva/i);
  assert.match(texto(fallo(503, {})), /volver a registrar más tarde/i, "sin texto del servicio, el propio");
  assert.match(texto(fallo(504, { error: "x" })), /No se ha podido mirar Sigrid/);
  assert.match(texto(fallo(504, { error: "x" })), /inocuo/);
  assert.match(texto(corte()), /No se ha podido mirar Sigrid/);
});

test("f040 R51, §3.2: el ensayo para y lo dice según el error, con lo propio de cada uno", () => {
  const texto = (error) => Volcado.siguientePaso({ fase: "ensayo", error: error }).mensaje;

  assert.match(texto(fallo(400, { error: "x", codigo: "peticion_invalida" })), /recarga/i);
  assert.match(texto(fallo(409, { error: "Hay que dar de alta la correspondencia, inventado", codigo: "usuario_sigrid_no_mapeado" })), /dar de alta la correspondencia, inventado/);
  assert.match(texto(fallo(409, { error: "x", codigo: "usuario_sigrid_inexistente" })), /07_alta_usuario_sigrid/);
  assert.match(
    texto(fallo(409, { error: "x", codigo: "volcado_rechazado_por_la_pasarela", codigo_pasarela: "obra_no_encontrada" })),
    new RegExp(Revision.textoMotivoVolcado("obra_no_encontrada")),
  );
  assert.match(texto(fallo(409, { error: "x", codigo: "bandeja_demasiado_grande", total: 10001 })), /10001/);
  assert.match(texto(fallo(502, { error: "x", codigo: "ensayo_sin_respuesta" })), /inocuo/);
  assert.match(texto(fallo(503, { error: "x", codigo: "sigrid_no_disponible" })), /Sigrid no responde/);
  assert.match(texto(fallo(503, { error: "x", codigo: "sigrid_no_disponible" })), /registrar más tarde/);
  assert.match(texto(fallo(409, { error: "x", codigo: "reclamaciones_sin_verificar", filas: 7000 })), /7000/);
  assert.match(texto(fallo(409, { error: "x", codigo: "obra_ambigua" })), /más de una obra/);
  assert.match(texto(fallo(503, { error: "x", codigo: "base_de_datos_no_disponible" })), /sistemas/);
  assert.match(texto(fallo(503, { error: "x", codigo: "configuracion_de_volcado_invalida" })), /sistemas/);
  assert.match(texto(corte()), /inocuo/);
  assert.doesNotMatch(texto(corte()), /en duda/);
});

test("f040 R53.3, §3.2: el volcado para y lo dice según el error: ventana cerrada, en duda, no se sabe", () => {
  const texto = (error) => Volcado.siguientePaso({ fase: "volcado", error: error }).mensaje;

  assert.match(texto(fallo(503, { error: "x", codigo: "volcado_deshabilitado" })), /ventana del volcado está cerrada/);
  assert.match(texto(fallo(503, { error: "x", codigo: "volcado_deshabilitado" })), /no se ha escrito nada/i);
  const sinRespuesta = texto(fallo(502, { error: "x", codigo: "volcado_sin_respuesta", en_duda: [ID(1)] }));
  assert.match(sinRespuesta, /en duda/);
  assert.match(sinRespuesta, /seguro/);
  assert.match(texto(fallo(500, { error: "x", codigo: "volcado_sin_traza" })), /en duda/);
  assert.match(texto(fallo(500, { error: "x", codigo: "volcado_sin_traza" })), /sistemas/);
  assert.match(texto(fallo(502, { error: "x", codigo: "ensayo_sin_respuesta" })), /antes de escribir|no se ha escrito nada/i);
  assert.match(texto(fallo(409, { error: "x", codigo: "ensayo_no_valido", motivo: "caducado" })), /ha caducado/);
  assert.match(texto(fallo(409, { error: "x", codigo: "ensayo_no_valido", motivo: "de_otra_persona" })), /otra persona/);
  const noSeSabe = texto(corte());
  assert.match(noSeSabe, /No se sabe/);
  assert.match(noSeSabe, /en duda/);
  assert.match(texto(fallo(503, { error: "x", codigo: "base_de_datos_no_disponible" })), /no se ha escrito nada/i);
});

test("f040 R54: un código de error desconocido sale tal cual, con el HTTP", () => {
  const paso = Volcado.siguientePaso({ fase: "volcado", error: fallo(418, { error: "texto inventado", codigo: "codigo_que_no_existe" }) });

  assert.match(paso.mensaje, /codigo_que_no_existe/);
  assert.match(paso.mensaje, /418/);
});

// --- R53.4, R59 · juntarVolcados y avisoDePte ---------------------------------------------------

test("f040 R53.4: juntarVolcados junta creados con su RS, ya creados, rechazados y no procesados con su motivo, excluidas y avisos", () => {
  const respuestas = [
    volcado(
      [hecho(1, "creado", "RS26.10/9030"), hecho(6, "idempotente", "RS26.10/9020"), hecho(3, "rechazado", null, "tipo_no_valido")],
      {
        excluidas: [{ incidencia_id: ID(9), motivo: "ya_volcada", sigrid_cod: null }],
        avisos: [{ incidencia_id: ID(1), referencia_externa: "PVI-" + ID(1), sigrid_cod_anterior: "RS26.10/9001", sigrid_cod: "RS26.10/9030" }],
      },
    ),
    volcado([hecho(7, "no_procesado", null, "presupuesto_de_tiempo_agotado")]),
  ];
  const r = Volcado.juntarVolcados(respuestas, null, []);

  assert.deepEqual(r.creados, [{ incidencia_id: ID(1), sigrid_cod: "RS26.10/9030" }]);
  assert.deepEqual(r.yaCreados, [{ incidencia_id: ID(6), sigrid_cod: "RS26.10/9020" }]);
  assert.deepEqual(r.rechazados.map((x) => [x.incidencia_id, x.texto]), [[ID(3), Revision.textoMotivoVolcado("tipo_no_valido")]]);
  assert.deepEqual(r.noProcesados.map((x) => [x.incidencia_id, x.texto]), [[ID(7), Revision.textoMotivoVolcado("presupuesto_de_tiempo_agotado")]]);
  assert.deepEqual(r.excluidas.map((x) => [x.incidencia_id, x.texto]), [[ID(9), Volcado.textoExclusion("ya_volcada")]]);
  assert.deepEqual(r.avisos, respuestas[0].avisos);
  assert.deepEqual(r.enDuda, []);
  assert.deepEqual(r.sinMandar, []);
  assert.deepEqual(r.resumen, { creados: 1, idempotentes: 1, rechazados: 1, no_procesados: 1, en_duda: 0, excluidas: 1, sin_mandar: 0 });
});

test("f040 R53.2, R53.4: en duda salen los sin_respuesta de un 200 y, del fallo, los de cada parada de §3.2", () => {
  const trozo = { ids: [ID(3), ID(5)] };
  const conSinRespuesta = Volcado.juntarVolcados([volcado([hecho(1, "creado", "RS26.10/9030"), hecho(6, "sin_respuesta")])], null, [ID(7)]);
  assert.deepEqual(conSinRespuesta.enDuda, [ID(6)]);
  assert.deepEqual(conSinRespuesta.sinMandar, [ID(7)]);

  const del502 = Volcado.juntarVolcados([], Object.assign({ error: fallo(502, { error: "x", codigo: "volcado_sin_respuesta", en_duda: [ID(5)] }) }, trozo), []);
  assert.deepEqual(del502.enDuda, [ID(5)], "502: solo las de su lista en_duda");
  assert.deepEqual(del502.sinMandar, [ID(3)], "la otra del trozo no consta como escrita: queda sin volcar");

  const del500 = Volcado.juntarVolcados([], Object.assign({ error: fallo(500, { error: "x", codigo: "volcado_sin_traza" }) }, trozo), []);
  assert.deepEqual(del500.enDuda, [ID(3), ID(5)], "500: las del trozo");

  const delCorte = Volcado.juntarVolcados([], Object.assign({ error: corte() }, trozo), [ID(7)]);
  assert.deepEqual(delCorte.enDuda, [ID(3), ID(5)], "sin respuesta: las del trozo, hasta volver a leer");
  assert.deepEqual(delCorte.sinMandar, [ID(7)]);

  const delCierre = Volcado.juntarVolcados([], Object.assign({ error: fallo(503, { error: "x", codigo: "volcado_deshabilitado" }) }, trozo), [ID(7)]);
  assert.deepEqual(delCierre.enDuda, [], "503: nada escrito, nada en duda");
  assert.deepEqual(delCierre.sinMandar, [ID(3), ID(5), ID(7)], "las del trozo, sin volcar, y las de después");
  assert.equal(delCierre.resumen.sin_mandar, 3);
});

test("f040 R59: avisoDePte solo con algún creado, y dice SAT, PTE y a mano", () => {
  const aviso = Volcado.avisoDePte({ creados: 2 });

  assert.match(aviso, /SAT/);
  assert.match(aviso, /PTE/);
  assert.match(aviso, /a mano/);
  assert.match(aviso, /2 partes/);
  assert.match(Volcado.avisoDePte({ creados: 1 }), /El parte creado queda/);
  assert.equal(Volcado.avisoDePte({ creados: 0, idempotentes: 3 }), "");
  assert.equal(Volcado.avisoDePte(null), "");
});

// --- R54 · un texto para cada código ------------------------------------------------------------

const MOTIVOS_DE_EXCLUSION = [
  "no_es_de_la_bandeja",
  "de_otra_obra",
  "no_es_candidata",
  "ya_volcada",
  "huella_no_coincide",
  "fuera_del_ensayo",
  "revision_desactualizada",
  "duplicada_en_sigrid",
  "conflicto_sin_confirmar",
];
const CAUSAS_ENSAYO_NO_VALIDO = ["no_existe", "de_otra_obra", "de_otra_persona", "caducado"];
const CODIGOS_DE_ERROR = [
  "peticion_invalida",
  "ensayo_no_valido",
  "usuario_sigrid_no_mapeado",
  "usuario_sigrid_inexistente",
  "volcado_rechazado_por_la_pasarela",
  "bandeja_demasiado_grande",
  "ensayo_sin_respuesta",
  "volcado_sin_respuesta",
  "volcado_sin_traza",
  "volcado_deshabilitado",
  "configuracion_de_volcado_invalida",
  "configuracion_sigrid_incompleta",
  "base_de_datos_no_disponible",
  "sigrid_no_disponible",
  "reclamaciones_sin_verificar",
  "obra_ambigua",
];

function textosPropios(funcion, codigos) {
  const textos = codigos.map((c) => funcion(c));
  for (const [i, texto] of textos.entries()) {
    assert.equal(typeof texto, "string", codigos[i]);
    assert.ok(texto.length > 0, `${codigos[i]}: sin texto`);
    assert.notEqual(texto, codigos[i], `${codigos[i]}: sale tal cual, sin traducir`);
    // Ajuste de T2 (2026-10-31): el texto de `usuario_sigrid_*` nombra el
    // script que da de alta la correspondencia (`infra/07_alta_usuario_sigrid.ps1`,
    // R54: decir qué hacer). Esa ruta no es un código; se quita antes de mirar.
    assert.doesNotMatch(texto.replace(/infra\/\S+/g, ""), /_/, `${codigos[i]}: el texto lleva un código`);
  }
  assert.equal(new Set(textos).size, textos.length, "un texto distinto para cada código");
}

test("f040 R54: un texto en castellano para CADA motivo de exclusión (F-059 y la guarda de F-065)", () => {
  textosPropios(Volcado.textoExclusion, MOTIVOS_DE_EXCLUSION);
  assert.deepEqual(Volcado.MOTIVOS_DE_EXCLUSION, MOTIVOS_DE_EXCLUSION);
});

test("f040 R54: un texto para CADA causa de ensayo_no_valido", () => {
  textosPropios(Volcado.textoEnsayoNoValido, CAUSAS_ENSAYO_NO_VALIDO);
  assert.deepEqual(Volcado.CAUSAS_ENSAYO_NO_VALIDO, CAUSAS_ENSAYO_NO_VALIDO);
});

test("f040 R54: un texto para CADA código de error de las rutas del volcado y de la sincronización", () => {
  textosPropios(Volcado.textoError, CODIGOS_DE_ERROR);
  assert.deepEqual(Volcado.CODIGOS_DE_ERROR, CODIGOS_DE_ERROR);
});

test("f040 R54, R61: un texto para cada veredicto, criterio y estado de parte", () => {
  textosPropios(Volcado.textoVeredicto, ["va", "se_enlaza", "ya_existe", "choca"]);
  textosPropios(Volcado.etiquetaParte, ["previsto", "idempotente", "rechazado", "no_procesado", "creado", "sin_respuesta"]);
  assert.equal(Volcado.etiquetaParte("previsto"), "Se crearía");
  assert.equal(Volcado.etiquetaParte("idempotente"), "Ya estaba creado");
  assert.equal(Volcado.etiquetaParte("rechazado"), "No se crea");
  assert.equal(Volcado.etiquetaParte("no_procesado"), "No se llegó a intentar");
});

test("f040 R54: un código desconocido sale tal cual; sin código, nada", () => {
  for (const funcion of [Volcado.textoExclusion, Volcado.textoEnsayoNoValido, Volcado.textoError, Volcado.etiquetaParte, Volcado.textoVeredicto]) {
    assert.equal(funcion("codigo_que_no_existe"), "codigo_que_no_existe");
    assert.equal(funcion(null), "");
    assert.equal(funcion(undefined), "");
    assert.equal(funcion("toString"), "toString", "nada heredado del prototipo");
  }
});

test("f040 R54: los códigos de §8.9 no se copian: los traduce Revision.textoMotivoVolcado", () => {
  const fuente = fs.readFileSync(path.join(__dirname, "..", "js", "volcado.js"), "utf-8");

  for (const codigo of Revision.MOTIVOS_DE_VOLCADO.concat(Revision.MOTIVOS_DE_LOTE)) {
    assert.ok(!fuente.includes(`${codigo}:`), `js/volcado.js copia el texto de ${codigo}`);
  }
  assert.match(fuente, /textoMotivoVolcado\(/);
});

// --- R55 · hayVolcadoEnMarcha --------------------------------------------------------------------

test("f040 R55: hayVolcadoEnMarcha solo con una serie de ensayos o de volcados en marcha; ilegible, no", () => {
  for (const fase of ["ensayando", "volcando"]) {
    assert.equal(Volcado.hayVolcadoEnMarcha({ volcado: { fase: fase } }), true, fase);
  }
  for (const fase of ["inicio", "sincronizando", "sincronizado", "ensayado", "terminado", "parado"]) {
    assert.equal(Volcado.hayVolcadoEnMarcha({ volcado: { fase: fase } }), false, fase);
  }
  assert.equal(Volcado.hayVolcadoEnMarcha({}), false);
  assert.equal(Volcado.hayVolcadoEnMarcha(null), false);
  const ilegible = {};
  Object.defineProperty(ilegible, "volcado", { get() { throw new Error("ilegible"); } });
  assert.equal(Volcado.hayVolcadoEnMarcha(ilegible), false);
});

test("f040 R50: resumenDelPanel cuenta aprobadas, en duda, volcadas, candidatas y trozos", () => {
  const r = Volcado.resumenDelPanel(panel(5));

  assert.deepEqual(
    [r.aprobadas, r.enDuda, r.volcadas, r.candidatas, r.trozos, r.partesPorLlamada],
    [7, 1, 3, 8, 2, 5],
  );
  assert.equal(r.texto, "8 candidatas, en 2 trozos de 5");
  assert.equal(Volcado.resumenDelPanel(panel(5, [ID(1)])).texto, "1 candidata, en 1 trozo de 5");
  assert.equal(Volcado.resumenDelPanel(panel(5, [])).texto, "Ninguna candidata");
});

// --- El componente: «Registrar» en su orden, con un api doble ------------------------------------

function apiDoble(guion) {
  const llamadas = [];
  const api = {};
  const nombres = ["identidad", "revision", "historialRevision", "accionRevision", "volcadoPanel", "revisionSigrid", "volcadoEnsayo", "volcadoVolcar"];
  for (const nombre of nombres) {
    api[nombre] = async (...args) => {
      llamadas.push({ nombre, args: JSON.parse(JSON.stringify(args)) });
      const paso = guion[nombre];
      const valor = Array.isArray(paso) ? paso.shift() : paso;
      const resuelto = typeof valor === "function" ? await valor(...args) : valor;
      if (resuelto instanceof Error) {
        throw resuelto;
      }
      return resuelto;
    };
  }
  return { api, llamadas };
}

function respuestaRevision() {
  return {
    obra: OBRA,
    catalogo: catalogo(),
    resumen: { total: 8, por_estado: { aprobada: 7, en_duda: 1 }, con_motivos: 0, por_motivo: {} },
    incidencias: [],
    siguiente: null,
    total_filtrado: 0,
  };
}

function relojDoble(inicio) {
  const reloj = {
    t: inicio === undefined ? AHORA : inicio,
    ticks: [],
    ahora() {
      return reloj.t;
    },
    cadaSegundo(funcion) {
      reloj.ticks.push(funcion);
      return () => {
        reloj.ticks = reloj.ticks.filter((f) => f !== funcion);
      };
    },
  };
  return reloj;
}

async function componente(guion, opciones) {
  const { api, llamadas } = apiDoble(
    Object.assign(
      {
        identidad: IDENTIDAD,
        revision: (obra) => Object.assign(respuestaRevision(), { obra: obra }),
        volcadoPanel: () => panel(2),
        revisionSigrid: () => sincronizacion(),
      },
      guion || {},
    ),
  );
  const reloj = (opciones && opciones.reloj) || relojDoble();
  const app = Volcado.conPanel(Revision.crearAppRevision({ api: api, parametros: "?obra=" + OBRA }), { api: api, reloj: reloj });
  await app.iniciar();
  return { app, llamadas, reloj };
}

function nombres(llamadas) {
  return llamadas.map((l) => l.nombre);
}

test("f040 R50, R56: cargar la obra pide GET /api/volcado (solo lee) y nada más; el panel enseña sus recuentos", async () => {
  const { app, llamadas } = await componente();

  assert.deepEqual(nombres(llamadas), ["identidad", "revision", "volcadoPanel"]);
  assert.deepEqual(llamadas[2].args, [OBRA]);
  assert.equal(app.volcado.obra, OBRA);
  assert.equal(app.volcado.panel.texto, "8 candidatas, en 4 trozos de 2");
  assert.deepEqual(app.volcado.candidatas, candidatas());
  assert.equal(app.volcado.fase, "inicio");
});

test("f040 R50: un fallo de GET /api/volcado se dice en el panel y no rompe la bandeja", async () => {
  const { app } = await componente({ volcadoPanel: () => fallo(503, { error: "Sin base, inventado.", codigo: "base_de_datos_no_disponible" }) });

  assert.equal(app.volcado.panel, null);
  assert.match(app.volcado.error, /Sin base, inventado\./);
  assert.equal(app.obraCargada, OBRA, "la bandeja sigue cargada");
  assert.equal(app.volcadoPuedeRegistrar(), false, "sin panel no se registra");
});

test("f040 R60: «Registrar» pide la sincronización UNA vez y nada más; enseña los grupos y espera", async () => {
  const { app, llamadas } = await componente();
  llamadas.length = 0;

  await app.registrar();

  assert.deepEqual(nombres(llamadas), ["revisionSigrid"]);
  assert.deepEqual(llamadas[0].args, [OBRA]);
  assert.equal(app.volcado.fase, "sincronizado");
  assert.deepEqual(app.volcado.grupos.va.map((f) => f.incidencia_id), [ID(1), ID(6), ID(7)]);
  assert.deepEqual(app.volcado.grupos.sinSincronizar, [ID(8)]);
  assert.equal(app.volcadoPuedeEnsayar(), true);
  assert.doesNotMatch(JSON.stringify(app.volcado), /ficha|FICTICIA DE LA FICHA/i, "R55: la ficha no se queda en la página");
});

test("f040 R60: el orden es sincronizar → enseñar → ensayar: sin el clic de ensayar, ningún ensayo", async () => {
  const { app, llamadas } = await componente({
    volcadoEnsayo: [ensayo([parte(1, "previsto"), parte(6, "previsto")]), ensayo([parte(7, "previsto")])],
  });

  assert.equal(app.volcadoPuedeEnsayar(), false, "antes de registrar no se puede ensayar");
  await app.ensayar();
  assert.ok(!nombres(llamadas).includes("volcadoEnsayo"), "ensayar sin sincronizar no hace nada");

  await app.registrar();
  assert.ok(!nombres(llamadas).includes("volcadoEnsayo"), "registrar no ensaya");

  await app.ensayar();
  assert.deepEqual(nombres(llamadas).slice(-2), ["volcadoEnsayo", "volcadoEnsayo"]);
  assert.ok(nombres(llamadas).indexOf("revisionSigrid") < nombres(llamadas).indexOf("volcadoEnsayo"));
});

for (const [que, error] of [
  ["400 peticion_invalida", fallo(400, { error: "x", codigo: "peticion_invalida" })],
  ["409 bandeja_demasiado_grande", fallo(409, { error: "x", codigo: "bandeja_demasiado_grande", total: 10001 })],
  ["409 reclamaciones_sin_verificar", fallo(409, { error: "x", codigo: "reclamaciones_sin_verificar", filas: 5001 })],
  ["409 obra_ambigua", fallo(409, { error: "x", codigo: "obra_ambigua" })],
  ["503 sin codigo", fallo(503, { error: "Sin Sigrid, inventado." })],
  ["504 del proxy", fallo(504, { error: "x" })],
  ["sin respuesta del servicio", corte()],
]) {
  test(`f040 R60: con la sincronización en ${que}, el panel para ahí: ni ensaya ni deja ensayar, y lo dice`, async () => {
    const { app, llamadas } = await componente({ revisionSigrid: () => error, volcadoEnsayo: () => ensayo([parte(1, "previsto")]) });

    await app.registrar();
    await app.ensayar();

    assert.equal(app.volcado.fase, "parado");
    assert.equal(app.volcado.grupos, null);
    assert.equal(app.volcadoPuedeEnsayar(), false);
    assert.equal(app.volcado.parada, Volcado.siguientePaso({ fase: "sincronizacion", error: error }).mensaje);
    assert.equal(nombres(llamadas).filter((n) => n === "revisionSigrid").length, 1, "una vez, sin reintento");
    assert.ok(!nombres(llamadas).includes("volcadoEnsayo"));
    assert.equal(app.volcadoTextoRegistrar(), "Volver a registrar");
  });
}

test("f040 R62: el ensayo lleva lo que va y lo incluido, por trozos de partes_por_llamada, con conflictos_confirmados del trozo", async () => {
  const { app, llamadas } = await componente({
    volcadoEnsayo: [ensayo([parte(1, "previsto"), parte(5, "previsto")]), ensayo([parte(6, "previsto"), parte(7, "previsto")])],
  });
  await app.registrar();
  app.volcado.incluidas[ID(5)] = true;
  app.volcado.incluidas[ID(2)] = true;

  await app.ensayar();

  const cuerpos = llamadas.filter((l) => l.nombre === "volcadoEnsayo").map((l) => l.args[0]);
  assert.deepEqual(cuerpos, [
    {
      obra: OBRA,
      usuario_oid: OID,
      usuario_correo: CORREO,
      incidencias: [ID(1), ID(5)],
      conflictos_confirmados: [{ incidencia_id: ID(5), sigrid_cods: ["RS26.10/9005", "RS26.10/9003"] }],
    },
    { obra: OBRA, usuario_oid: OID, usuario_correo: CORREO, incidencias: [ID(6), ID(7)] },
  ]);
  assert.equal(app.volcado.fase, "ensayado");
  assert.deepEqual(app.volcado.progreso, { k: 2, m: 2 });
});

test("f040 R51: la serie de ensayos para en el primer no-200: no pide los trozos siguientes y no deja volcar", async () => {
  const { app, llamadas } = await componente({
    volcadoPanel: () => panel(1),
    volcadoEnsayo: [ensayo([parte(1, "previsto")]), fallo(502, { error: "x", codigo: "ensayo_sin_respuesta" }), ensayo([parte(7, "previsto")])],
  });
  await app.registrar();

  await app.ensayar();

  assert.equal(nombres(llamadas).filter((n) => n === "volcadoEnsayo").length, 2);
  assert.equal(app.volcado.fase, "parado");
  assert.match(app.volcado.parada, /inocuo/);
  assert.equal(app.volcadoPuedeVolcar(), false);
  assert.deepEqual(app.volcado.progreso, { k: 2, m: 3 });
});

test("f040 R51: un corte en un ensayo también para la serie", async () => {
  const { app, llamadas } = await componente({
    volcadoPanel: () => panel(1),
    volcadoEnsayo: [corte(), ensayo([parte(6, "previsto")])],
  });
  await app.registrar();

  await app.ensayar();

  assert.equal(nombres(llamadas).filter((n) => n === "volcadoEnsayo").length, 1);
  assert.equal(app.volcado.fase, "parado");
});

test("f040 R62: lo que la guarda excluye porque cambió desde la sincronización se enseña y se propone volver a registrar", async () => {
  const { app } = await componente({
    volcadoPanel: () => panel(5),
    volcadoEnsayo: [ensayo([parte(1, "previsto")], [{ incidencia_id: ID(6), motivo: "duplicada_en_sigrid", sigrid_cod: "RS26.10/9010" }])],
  });
  await app.registrar();

  await app.ensayar();

  assert.equal(app.volcado.fase, "ensayado", "no es un fallo: la serie sigue");
  assert.equal(app.volcado.guarda.hayCambios, true);
  assert.equal(app.volcado.guarda.excluidas[0].incidencia_id, ID(6));
  assert.equal(app.volcadoTextoRegistrar(), "Volver a registrar");
});

test("f040 R53.5: tras una serie de ensayos con algún idempotente se relee el panel y la primera página de la bandeja", async () => {
  const { app, llamadas } = await componente({
    volcadoPanel: () => panel(5),
    volcadoEnsayo: [ensayo([parte(1, "idempotente", { sigrid_cod: "RS26.10/9001" }), parte(6, "previsto")])],
  });
  await app.registrar();
  llamadas.length = 0;

  await app.ensayar();

  assert.deepEqual(nombres(llamadas), ["volcadoEnsayo", "revision", "volcadoPanel"]);
  assert.equal(app.volcado.fase, "ensayado", "releer no borra el ensayo");
  assert.equal(app.volcadoPuedeVolcar(), true);
});

test("f040 R53.5: sin idempotentes, tras ensayar no se relee nada", async () => {
  const { app, llamadas } = await componente({ volcadoPanel: () => panel(5), volcadoEnsayo: [ensayo([parte(1, "previsto")])] });
  await app.registrar();
  llamadas.length = 0;

  await app.ensayar();

  assert.deepEqual(nombres(llamadas), ["volcadoEnsayo"]);
});

async function ensayado(guion, opciones) {
  const preparado = await componente(
    Object.assign(
      {
        volcadoPanel: () => panel(2),
        volcadoEnsayo: [ensayo([parte(1, "previsto"), parte(6, "previsto")]), ensayo([parte(7, "previsto")])],
      },
      guion || {},
    ),
    opciones,
  );
  await preparado.app.registrar();
  await preparado.app.ensayar();
  preparado.llamadas.length = 0;
  return preparado;
}

test("f040 R52, D-12: volcar pide un segundo clic y teclear N; sin eso no sale nada", async () => {
  const { app, llamadas } = await ensayado({ volcadoVolcar: () => volcado([]) });

  await app.volcar();
  assert.deepEqual(nombres(llamadas), [], "sin el primer clic, nada");

  app.pedirVolcado();
  assert.equal(app.volcado.confirmando, true);
  assert.equal(
    app.volcadoConfirmacion(),
    "Se van a crear 3 partes en el ERP de producción de la obra 9901: 2 de VILLA 91 y 1 de 9901-03. Escribe 3 para confirmar.",
  );
  app.volcado.tecleado = "2";
  assert.equal(app.volcadoConfirmacionValida(), false);
  await app.volcar();
  assert.deepEqual(nombres(llamadas), [], "con otro número, nada");

  app.cancelarVolcado();
  assert.equal(app.volcado.confirmando, false);
  app.volcado.tecleado = "3";
  await app.volcar();
  assert.deepEqual(nombres(llamadas), [], "cancelado, nada aunque el número sea bueno");
});

test("f040 R52, R53: con la confirmación, un volcado por ensayo con previstos, de uno en uno y en su orden", async () => {
  const { app, llamadas } = await ensayado({
    volcadoVolcar: [
      volcado([hecho(1, "creado", "RS26.10/9030"), hecho(6, "creado", "RS26.10/9031")]),
      volcado([hecho(7, "creado", "RS26.10/9032")]),
    ],
  });
  app.pedirVolcado();
  app.volcado.tecleado = "3";

  await app.volcar();

  const cuerpos = llamadas.filter((l) => l.nombre === "volcadoVolcar").map((l) => l.args[0]);
  assert.deepEqual(cuerpos.map((c) => c.incidencias.map((i) => i.incidencia_id)), [[ID(1), ID(6)], [ID(7)]]);
  assert.ok(cuerpos.every((c) => c.confirmado === true && c.usuario_oid === OID && c.usuario_correo === CORREO));
  assert.equal(app.volcado.fase, "terminado");
  assert.deepEqual(app.volcado.resultado.creados.map((c) => c.sigrid_cod), ["RS26.10/9030", "RS26.10/9031", "RS26.10/9032"]);
  assert.match(app.volcado.aviso, /PTE/);
  assert.deepEqual(nombres(llamadas).slice(-2), ["revision", "volcadoPanel"], "R53.5: al terminar relee");
  assert.equal(app.volcadoPuedeVolcar(), false, "lo volcado no se vuelve a volcar con el mismo ensayo");
});

test("f040 R52: un ensayo sin previstos no se manda (el backend rechaza una lista vacía)", async () => {
  const { app, llamadas } = await ensayado({
    volcadoEnsayo: [ensayo([parte(1, "idempotente"), parte(6, "rechazado", { motivo: "tipo_no_valido" })]), ensayo([parte(7, "previsto")])],
    volcadoVolcar: [volcado([hecho(7, "creado", "RS26.10/9032")])],
  });
  app.pedirVolcado();
  app.volcado.tecleado = "1";

  await app.volcar();

  const cuerpos = llamadas.filter((l) => l.nombre === "volcadoVolcar").map((l) => l.args[0]);
  assert.equal(cuerpos.length, 1);
  assert.deepEqual(cuerpos[0].incidencias, [{ incidencia_id: ID(7), revision_id: ID(207) }]);
});

for (const [que, paso, esperado] of [
  ["503 volcado_deshabilitado", fallo(503, { error: "x", codigo: "volcado_deshabilitado" }), { enDuda: [], sinMandar: [ID(1), ID(6), ID(7)] }],
  ["502 volcado_sin_respuesta", fallo(502, { error: "x", codigo: "volcado_sin_respuesta", en_duda: [ID(6)] }), { enDuda: [ID(6)], sinMandar: [ID(1), ID(7)] }],
  ["500 volcado_sin_traza", fallo(500, { error: "x", codigo: "volcado_sin_traza" }), { enDuda: [ID(1), ID(6)], sinMandar: [ID(7)] }],
  ["409 ensayo_no_valido", fallo(409, { error: "x", codigo: "ensayo_no_valido", motivo: "caducado" }), { enDuda: [], sinMandar: [ID(1), ID(6), ID(7)] }],
  ["400 peticion_invalida", fallo(400, { error: "x", codigo: "peticion_invalida" }), { enDuda: [], sinMandar: [ID(1), ID(6), ID(7)] }],
  ["sin respuesta del servicio", corte(), { enDuda: [ID(1), ID(6)], sinMandar: [ID(7)] }],
  ["200 con un sin_respuesta", volcado([hecho(1, "creado", "RS26.10/9030"), hecho(6, "sin_respuesta")]), { enDuda: [ID(6)], sinMandar: [ID(7)] }],
]) {
  test(`f040 R53.2: un volcado con ${que} para: no manda el siguiente, enseña qué quedó y relee`, async () => {
    const { app, llamadas } = await ensayado({ volcadoVolcar: [paso, volcado([hecho(7, "creado", "RS26.10/9032")])] });
    app.pedirVolcado();
    app.volcado.tecleado = "3";

    await app.volcar();

    assert.equal(nombres(llamadas).filter((n) => n === "volcadoVolcar").length, 1, "no se manda el siguiente");
    assert.equal(app.volcado.fase, "parado");
    assert.deepEqual(app.volcado.resultado.enDuda, esperado.enDuda);
    assert.deepEqual(app.volcado.resultado.sinMandar, esperado.sinMandar);
    assert.ok(app.volcado.parada.length > 0);
    assert.deepEqual(nombres(llamadas).slice(-2), ["revision", "volcadoPanel"], "R53.5: al parar relee");
    assert.equal(app.volcadoTextoRegistrar(), "Volver a registrar");
  });
}

test("f040 R53.1: con el ensayo de un trozo caducado, ese trozo no se manda y el panel para", async () => {
  const reloj = relojDoble();
  const { app, llamadas } = await ensayado(
    {
      volcadoEnsayo: [ensayo([parte(1, "previsto"), parte(6, "previsto")], [], CADUCA), ensayo([parte(7, "previsto")], [], CADUCA)],
      volcadoVolcar: [() => {
        reloj.t = Date.parse(CADUCA) + 1;
        return volcado([hecho(1, "creado", "RS26.10/9030"), hecho(6, "creado", "RS26.10/9031")]);
      }],
    },
    { reloj: reloj },
  );
  app.pedirVolcado();
  app.volcado.tecleado = "3";

  await app.volcar();

  assert.equal(nombres(llamadas).filter((n) => n === "volcadoVolcar").length, 1);
  assert.equal(app.volcado.fase, "parado");
  assert.match(app.volcado.parada, /caducado/);
  assert.match(app.volcado.parada, /volver a registrar/i);
  assert.deepEqual(app.volcado.resultado.sinMandar, [ID(7)]);
  assert.equal(app.volcado.resultado.creados.length, 2);
});

test("f040 R52: con el ensayo ya caducado al confirmar, no sale nada", async () => {
  const reloj = relojDoble();
  const { app, llamadas } = await ensayado({ volcadoVolcar: () => volcado([]) }, { reloj: reloj });
  app.pedirVolcado();
  app.volcado.tecleado = "3";
  reloj.t = Date.parse(CADUCA);

  await app.volcar();

  assert.deepEqual(nombres(llamadas), []);
  assert.equal(app.volcadoPuedeVolcar(), false);
});

test("f040 R56, R55: con una serie en marcha, ni registrar, ni ensayar, ni volcar; y la guarda lo sabe", async () => {
  let soltar;
  const pendiente = new Promise((resolver) => {
    soltar = resolver;
  });
  const { app, llamadas } = await componente({ volcadoPanel: () => panel(5), volcadoEnsayo: [() => pendiente] });
  await app.registrar();

  const enCurso = app.ensayar();
  await Promise.resolve();
  assert.equal(app.volcado.fase, "ensayando");
  assert.equal(app.volcado.enVuelo, true);
  assert.equal(app.hayVolcadoEnMarcha(), true);
  assert.equal(Volcado.hayVolcadoEnMarcha(app), true);
  assert.equal(app.volcadoPuedeRegistrar(), false);
  assert.equal(app.volcadoPuedeEnsayar(), false);
  await app.registrar();
  await app.ensayar();
  assert.equal(nombres(llamadas).filter((n) => n === "revisionSigrid").length, 1, "registrar en vuelo no sale");
  assert.equal(nombres(llamadas).filter((n) => n === "volcadoEnsayo").length, 1, "ensayar en vuelo no sale");

  soltar(ensayo([parte(1, "previsto")]));
  await enCurso;
  assert.equal(app.hayVolcadoEnMarcha(), false);
  assert.equal(app.volcado.enVuelo, false);
});

test("f040 R56: sin la sesión completa (oid y correo) no se ensaya ni se vuelca", async () => {
  const { app, llamadas } = await componente({ identidad: { usuarioOid: OID, correo: "" }, volcadoEnsayo: () => ensayo([parte(1, "previsto")]) });
  await app.registrar();

  assert.equal(app.volcadoPuedeEnsayar(), false);
  await app.ensayar();
  assert.ok(!nombres(llamadas).includes("volcadoEnsayo"));
});

test("f040 R53.6: «Volver a registrar» repite desde la sincronización y limpia el ensayo y el resultado", async () => {
  const { app, llamadas } = await ensayado({ volcadoVolcar: [fallo(503, { error: "x", codigo: "volcado_deshabilitado" })] });
  app.pedirVolcado();
  app.volcado.tecleado = "3";
  await app.volcar();
  llamadas.length = 0;

  await app.registrar();

  assert.deepEqual(nombres(llamadas), ["revisionSigrid"]);
  assert.equal(app.volcado.fase, "sincronizado");
  assert.deepEqual(app.volcado.ensayos, []);
  assert.equal(app.volcado.resultado, null);
  assert.equal(app.volcado.parada, "");
  assert.deepEqual(app.volcado.incluidas, {});
});

test("f040 R50: cargar otra obra deja el panel a cero; volver a leer la misma no borra lo ensayado", async () => {
  const { app } = await ensayado();

  await app.cargar();
  assert.equal(app.volcado.fase, "ensayado", "misma obra: se conserva");

  app.obra = "9902";
  await app.cargar();
  assert.equal(app.volcado.obra, "9902");
  assert.equal(app.volcado.fase, "inicio");
  assert.equal(app.volcado.grupos, null);
  assert.deepEqual(app.volcado.ensayos, []);
});

test("f040 R52: la cuenta atrás corre con el reloj y se para al volcar", async () => {
  const reloj = relojDoble();
  const { app } = await ensayado({ volcadoVolcar: [volcado([]), volcado([])] }, { reloj: reloj });

  assert.equal(app.volcadoCuentaAtras(), "30:00");
  assert.equal(reloj.ticks.length, 1, "un solo reloj en marcha");
  reloj.t += 90 * 1000;
  reloj.ticks[0]();
  assert.equal(app.volcadoCuentaAtras(), "28:30");

  app.pedirVolcado();
  app.volcado.tecleado = "3";
  await app.volcar();
  assert.equal(reloj.ticks.length, 0, "volcado, el reloj se para");
});

test("f040 R59: sin ningún creado, no hay aviso de PTE", async () => {
  const { app } = await ensayado({ volcadoVolcar: [volcado([hecho(1, "idempotente", "RS26.10/9001"), hecho(6, "idempotente", "RS26.10/9002")]), volcado([hecho(7, "rechazado", null, "tipo_no_valido")])] });
  app.pedirVolcado();
  app.volcado.tecleado = "3";

  await app.volcar();

  assert.equal(app.volcado.aviso, "");
  assert.equal(app.volcado.fase, "terminado");
});

test("f040 R53.4: los avisos de posible duplicado llegan al resultado", async () => {
  const aviso = { incidencia_id: ID(1), referencia_externa: "PVI-" + ID(1), sigrid_cod_anterior: "RS26.10/9001", sigrid_cod: "RS26.10/9030" };
  const { app } = await ensayado({ volcadoVolcar: [volcado([hecho(1, "creado", "RS26.10/9030"), hecho(6, "creado", "RS26.10/9031")], { avisos: [aviso] }), volcado([hecho(7, "creado", "RS26.10/9032")])] });
  app.pedirVolcado();
  app.volcado.tecleado = "3";

  await app.volcar();

  assert.deepEqual(app.volcado.resultado.avisos, [aviso]);
});

test("f040 R55: ni el correo ni el oid se escriben en consola ni en el almacenamiento durante todo el recorrido", async () => {
  const escrito = [];
  const originales = {};
  for (const metodo of ["log", "info", "warn", "error", "debug"]) {
    originales[metodo] = console[metodo];
    console[metodo] = (...args) => escrito.push(args.map(String).join(" "));
  }
  const almacen = {};
  global.localStorage = { setItem: (k, v) => { almacen[k] = v; }, getItem: () => null };
  global.sessionStorage = global.localStorage;
  try {
    const { app } = await ensayado({ volcadoVolcar: [volcado([hecho(1, "creado", "RS26.10/9030")]), corte()] });
    app.pedirVolcado();
    app.volcado.tecleado = "3";
    await app.volcar();
  } finally {
    Object.assign(console, originales);
    delete global.localStorage;
    delete global.sessionStorage;
  }

  assert.deepEqual(escrito, []);
  assert.deepEqual(almacen, {});
});

// --- bandeja.html · el panel, evaluado contra el componente ----------------------------------

const BANDEJA_HTML = path.join(__dirname, "..", "bandeja.html");

function leerBandeja() {
  return fs.readFileSync(BANDEJA_HTML, "utf-8");
}

/** Lo que pinta el panel (lo de dentro de `section#volcado`). */
function delPanel(elementos) {
  return elementos.filter((e) => e.antepasados.some((a) => a.atributos.id === "volcado") || e.atributos.id === "volcado");
}

async function alcanceAbierto() {
  const { app } = await ensayado({ volcadoVolcar: [volcado([hecho(1, "creado", "RS26.10/9030"), hecho(6, "sin_respuesta")]), volcado([])] });
  const alcance = Object.create(app);
  alcance.volcado = Object.assign({}, app.volcado, {
    confirmando: true,
    tecleado: "3",
    parada: "parada inventada",
    resultado: Volcado.juntarVolcados(
      [
        volcado([hecho(1, "creado", "RS26.10/9030"), hecho(6, "sin_respuesta"), hecho(3, "rechazado", null, "tipo_no_valido"), hecho(5, "no_procesado", null, "presupuesto_de_tiempo_agotado"), hecho(4, "idempotente", "RS26.10/9004")], {
          excluidas: [{ incidencia_id: ID(9), motivo: "ya_volcada", sigrid_cod: null }],
          avisos: [{ incidencia_id: ID(1), referencia_externa: "PVI-" + ID(1), sigrid_cod_anterior: "RS26.10/9001", sigrid_cod: "RS26.10/9030" }],
        }),
      ],
      null,
      [ID(7)],
    ),
    aviso: Volcado.avisoDePte({ creados: 1 }),
    guarda: Volcado.excluidasDeLaGuarda([ensayo([], [{ incidencia_id: ID(6), motivo: "duplicada_en_sigrid", sigrid_cod: "RS26.10/9010" }])], app.volcado.grupos),
    error: "error inventado",
  });
  alcance.volcado.incluidas = { [ID(3)]: true };
  return alcance;
}

test("f040 R50: cada expresión del panel de bandeja.html se evalúa contra el componente sin error, con todo abierto", async () => {
  const { elementos, problemas } = recorrer(leerBandeja(), await alcanceAbierto());
  const panelPintado = delPanel(elementos);

  assert.deepEqual(problemas, []);
  assert.ok(panelPintado.length > 60, `el panel pinta ${panelPintado.length} elementos con todo abierto: ¿se ha leído?`);
});

test("f040 R50: control: un nombre que el componente no tiene, en el panel, salta", async () => {
  const html = leerBandeja();
  const alcance = await alcanceAbierto();
  for (const [viejo, nuevo] of [
    ['@click="registrar()"', '@click="registrarla()"'],
    // Ajuste de T2 (2026-10-31): `volcado.panel.textos` era un mal control —una
    // propiedad que falta da `undefined`, no un error, también en Alpine—; un
    // objeto que falta sí lanza, que es lo que el recorrido tiene que ver.
    ['x-text="volcado.panel.texto"', 'x-text="volcado.paneles.texto"'],
  ]) {
    assert.ok(html.includes(viejo), `el control no encuentra ${viejo}`);
    const { problemas } = recorrer(html.replace(viejo, nuevo), alcance);
    assert.notDeepEqual(problemas, [], `${nuevo}: el recorrido no lo ve`);
  }
});

function botonesDelPanel(elementos) {
  return delPanel(elementos).filter((e) => e.nombre === "button");
}

function metodoDelClic(e) {
  const m = (e.atributos["@click"] || "").match(/^\s*([\w$.]+)\s*\(/);
  return m ? m[1] : null;
}

test("f040 R50, R56: con la obra recién cargada, el único botón del panel es «Registrar»", async () => {
  const { app } = await componente();
  const { elementos, problemas } = recorrer(leerBandeja(), app);

  assert.deepEqual(problemas, []);
  const visibles = botonesDelPanel(elementos).filter((e) => e.visible);
  assert.deepEqual(visibles.map(metodoDelClic), ["registrar"]);
  assert.equal(Boolean(evaluarEn(visibles[0].alcance, visibles[0].atributos[":disabled"])), false, "habilitado");
});

test("f040 R62: lo que ya existe no tiene casilla ni botón; lo que choca, una casilla por incidencia", async () => {
  const { app } = await componente();
  await app.registrar();
  const html = leerBandeja();
  const { elementos } = recorrer(html, app);
  const casillas = delPanel(elementos).filter((e) => e.nombre === "input" && e.atributos.type === "checkbox");

  assert.ok(casillas.length >= 1, "hay casilla en lo que choca");
  for (const casilla of casillas) {
    assert.match(casilla.atributos["x-model"], /^volcado\.incluidas\[fila\.incidencia_id\]$/);
    assert.ok(
      casilla.antepasados.some((a) => /volcado\.grupos\.choca/.test(a.atributos["x-for"] || "")),
      "la casilla está dentro del x-for de choca",
    );
  }
  const enYaExiste = delPanel(elementos).filter(
    (e) => e.antepasados.some((a) => /volcado\.grupos\.ya_existe/.test(a.atributos["x-for"] || "")) && ["input", "button"].includes(e.nombre),
  );
  assert.deepEqual(enYaExiste, [], "ningún control en lo que ya existe");
  assert.doesNotMatch(html, /ya_existe[^"]*incluidas|incluidas[^"]*ya_existe/, "nada incluye lo que ya existe");
});

test("f040 R56: con una petición en vuelo, ningún botón de registrar, ensayar ni volcar se puede pulsar", async () => {
  const { elementos } = recorrer(leerBandeja(), await alcanceAbierto());
  const botones = botonesDelPanel(elementos).filter((e) => ["registrar", "ensayar", "pedirVolcado", "volcar"].includes(metodoDelClic(e)));

  assert.deepEqual([...new Set(botones.map(metodoDelClic))].sort(), ["ensayar", "pedirVolcado", "registrar", "volcar"]);
  for (const boton of botones) {
    const alcance = Object.create(boton.alcance);
    alcance.volcado = Object.assign({}, boton.alcance.volcado, { enVuelo: true });
    assert.ok(":disabled" in boton.atributos, `${metodoDelClic(boton)} lleva :disabled`);
    assert.equal(Boolean(evaluarEn(alcance, boton.atributos[":disabled"])), true, metodoDelClic(boton));
  }
});

test("f040 R52: el botón de volcar sin la confirmación válida no se puede pulsar; con ella, sí", async () => {
  const alcanceBase = await alcanceAbierto();
  const { elementos } = recorrer(leerBandeja(), alcanceBase);
  const volcar = botonesDelPanel(elementos).find((e) => metodoDelClic(e) === "volcar");

  for (const [tecleado, deshabilitado] of [["3", false], ["2", true], ["", true]]) {
    const alcance = Object.create(volcar.alcance);
    alcance.volcado = Object.assign({}, volcar.alcance.volcado, { tecleado: tecleado });
    assert.equal(Boolean(evaluarEn(alcance, volcar.atributos[":disabled"])), deshabilitado, tecleado);
  }
});

// --- R55 · la guarda de salida, una y ampliada -------------------------------------------------

function guardaDeSalida() {
  const enLinea = [...leerBandeja().matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  assert.equal(enLinea.length, 1, "bandeja.html lleva un único <script> en línea: la guarda de salida");
  return enLinea[0];
}

function salirCon(estado, ventanaExtra) {
  const escuchas = [];
  const ventana = Object.assign(
    { addEventListener: (tipo, funcion) => escuchas.push({ tipo, funcion }), Revision: Revision, Volcado: Volcado, Alpine: { $data: () => estado } },
    ventanaExtra || {},
  );
  require("node:vm").runInNewContext(guardaDeSalida(), { window: ventana, document: { querySelector: () => ({}) } });
  const evento = { prevenido: false, returnValue: undefined, preventDefault() { this.prevenido = true; } };
  for (const e of escuchas) e.funcion(evento);
  return { escuchas, evento };
}

test("f040 R55: la guarda de salida (una) pregunta con un volcado en marcha y no sin él", () => {
  const conSerie = salirCon({ formulario: null, volcado: { fase: "volcando" } });
  assert.deepEqual(conSerie.escuchas.map((e) => e.tipo), ["beforeunload"]);
  assert.equal(conSerie.evento.prevenido, true);
  assert.equal(salirCon({ formulario: null, volcado: { fase: "ensayando" } }).evento.prevenido, true);
  assert.equal(salirCon({ formulario: null, volcado: { fase: "ensayado" } }).evento.prevenido, false);
  assert.equal(salirCon({ formulario: null, volcado: { fase: "inicio" } }).evento.prevenido, false);
});

test("f040 R55: la guarda sigue preguntando por la edición sin guardar de F-038, y sin Volcado no lanza", () => {
  const formulario = Revision.formularioDe(
    { unidad_codigo: "9901-01", ubicacion: null, descripcion: "x", detalle: null, oficio_codigo: null, proveedor_codigo: null, urgencia: null, listado: null },
    catalogo(),
  );
  formulario.descripcion = "otra";
  assert.equal(salirCon({ formulario: formulario, volcado: { fase: "inicio" } }).evento.prevenido, true);
  assert.equal(salirCon({ formulario: null, volcado: { fase: "volcando" } }, { Volcado: undefined }).evento.prevenido, false);
});
