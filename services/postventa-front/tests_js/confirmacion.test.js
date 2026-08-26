// services/postventa-front/tests_js/confirmacion.test.js
// R19 · La confirmación en dos pasos antes de archivar.
//
// Es lo único que separa un clic accidental de UNA TANDA DE SUBIDAS REALES a
// SharePoint. Hasta la review de F-007 vivía suelta en `js/app.js`, que el
// diseño deja sin tests a propósito: es decir, no la comprobaba nada.
//
// Todo se prueba con un reloj pasado por parámetro: ni un `setTimeout`, ni un
// `Date.now()` real. Un test de caducidad que dependa del reloj de la máquina
// es un test que falla en la máquina de otro.

const test = require("node:test");
const assert = require("node:assert/strict");

const Confirmacion = require("../js/confirmacion.js");

/** Un instante cualquiera, para no depender del reloj de nadie. */
const T0 = 1_000_000;

test("f007 R19: sin armar, un solo clic NO dispara nada", () => {
  const decision = Confirmacion.resolver(null, T0);

  assert.equal(decision.dispara, false);
  assert.equal(decision.motivo, "sin_armar");
  assert.equal(decision.estado, null);
});

test("f007 R19: el segundo clic sí dispara", () => {
  const armada = Confirmacion.armar(T0);

  const decision = Confirmacion.resolver(armada, T0 + 1_000);

  assert.equal(decision.dispara, true);
  assert.equal(decision.motivo, "");
});

test("f007 R19: tras disparar, la confirmación queda desarmada", () => {
  // Defensa contra el doble clic sobre «Sí, archivar»: el mismo armado no
  // puede disparar dos tandas de subidas.
  const armada = Confirmacion.armar(T0);

  const primera = Confirmacion.resolver(armada, T0 + 1_000);
  assert.equal(primera.dispara, true);
  assert.equal(primera.estado, null, "resolver debe devolver el estado desarmado");

  const segunda = Confirmacion.resolver(primera.estado, T0 + 1_100);
  assert.equal(segunda.dispara, false);
  assert.equal(segunda.motivo, "sin_armar");
});

test("f007 R19: una confirmación olvidada caduca y NO dispara", () => {
  // El usuario arma, se va, y alguien pulsa al volver. Eso no puede subir
  // nada a SharePoint.
  const armada = Confirmacion.armar(T0);

  const decision = Confirmacion.resolver(armada, T0 + Confirmacion.VENTANA_MS + 1);

  assert.equal(decision.dispara, false);
  assert.equal(decision.motivo, "caducada");
  assert.equal(decision.estado, null, "al caducar se vuelve al estado inicial");
});

test("f007 R19: justo en el borde de la ventana todavía dispara", () => {
  const armada = Confirmacion.armar(T0);

  const decision = Confirmacion.resolver(armada, T0 + Confirmacion.VENTANA_MS);

  assert.equal(decision.dispara, true);
});

test("f007 R19: la ventana se puede acortar para probarla", () => {
  const armada = Confirmacion.armar(T0);

  assert.equal(Confirmacion.resolver(armada, T0 + 10, 5).dispara, false);
  assert.equal(Confirmacion.resolver(armada, T0 + 4, 5).dispara, true);
});

test("f007 R19: un reloj que va hacia atrás no dispara", () => {
  // Un salto de reloj (cambio de hora, sincronización NTP) no es una
  // confirmación válida: ante la duda, no se sube nada.
  const armada = Confirmacion.armar(T0);

  const decision = Confirmacion.resolver(armada, T0 - 1);

  assert.equal(decision.dispara, false);
  assert.equal(decision.motivo, "caducada");
});

test("f007 R19: un estado corrupto no dispara", () => {
  for (const basura of [{}, { armadaEn: "ayer" }, { armadaEn: NaN }, undefined, 0, ""]) {
    const decision = Confirmacion.resolver(basura, T0);
    assert.equal(decision.dispara, false, `${JSON.stringify(basura)} ha disparado`);
    assert.equal(decision.motivo, "sin_armar");
  }
});

test("f007 R19: resolver NO muta el estado que recibe", () => {
  const armada = Confirmacion.armar(T0);
  const copia = { armadaEn: armada.armadaEn };

  Confirmacion.resolver(armada, T0 + 1);

  assert.deepEqual(armada, copia, "resolver ha tocado el estado de quien llama");
});

test("f007 R19: pendiente() dice si hay que pintar el «¿seguro?»", () => {
  assert.equal(Confirmacion.pendiente(null), false);
  assert.equal(Confirmacion.pendiente(Confirmacion.armar(T0)), true);
  // Caducada NO se puede saber al pintar: el reloj no es reactivo. El panel
  // sigue visible y es el clic el que descubre la caducidad. Que `pendiente`
  // no mire el reloj es deliberado.
  assert.equal(Confirmacion.pendiente({}), false);
});

test("f007 R19: cancelar deja la confirmación sin armar", () => {
  assert.equal(Confirmacion.cancelar(), null);
  assert.equal(Confirmacion.pendiente(Confirmacion.cancelar()), false);
});

test("f007 R19: armar exige un reloj de verdad", () => {
  for (const malo of [undefined, null, NaN, "ahora", Infinity]) {
    assert.throws(
      () => Confirmacion.armar(malo),
      /reloj/i,
      `armar(${String(malo)}) debería haber lanzado`,
    );
  }
});

test("f007 R19: la ventana por defecto es un tiempo humano", () => {
  // Ni cero (imposible confirmar) ni una hora (no protege de nada).
  assert.ok(Number.isFinite(Confirmacion.VENTANA_MS));
  assert.ok(Confirmacion.VENTANA_MS >= 5_000);
  assert.ok(Confirmacion.VENTANA_MS <= 300_000);
});

// --- F-009 R15 · la misma confirmacion, ahora tambien para el cierre --------
//
// F-009 reutiliza este modulo TAL CUAL y no escribe uno paralelo: la
// caducidad, el doble clic y el reloj hacia atras son el mismo problema, y dos
// implementaciones del mismo control divergen siempre. Lo unico que cambia es
// el texto, porque tiene que nombrar el boton que el usuario va a volver a
// pulsar.
//
// Lo que hay detras del cierre no es una tanda de subidas: es una ESCRITURA EN
// EL ERP DE PRODUCCION. Por eso los tres casos se repiten aqui explicitamente
// en vez de darlos por probados.

test("f009 R15: un solo clic no cierra ninguna incidencia", () => {
  const decision = Confirmacion.resolver(null, 1000);

  assert.equal(decision.dispara, false);
  assert.equal(decision.motivo, Confirmacion.SIN_ARMAR);
});

test("f009 R15: un segundo clic fuera de la ventana NO dispara el cierre", () => {
  const armada = Confirmacion.armar(1000);

  const decision = Confirmacion.resolver(armada, 1000 + Confirmacion.VENTANA_MS + 1);

  assert.equal(decision.dispara, false);
  assert.equal(decision.motivo, Confirmacion.CADUCADA);
  assert.equal(decision.estado, null);
});

test("f009 R15: y el armado queda consumido, asi que el doble clic no cierra dos veces", () => {
  const armada = Confirmacion.armar(1000);

  const primera = Confirmacion.resolver(armada, 1500);
  const segunda = Confirmacion.resolver(primera.estado, 1600);

  assert.equal(primera.dispara, true);
  assert.equal(segunda.dispara, false);
});

test("f009 R15: el aviso de caducidad nombra el boton del cierre", () => {
  const aviso = Confirmacion.avisoCaducada("cierre");

  assert.match(aviso, /Cerrar/);
  assert.notEqual(aviso, Confirmacion.AVISO_CADUCADA);
});

test("f009 R15: y para cualquier otra accion sigue siendo el de archivar", () => {
  // Sin esto, el dia que alguien pase una accion nueva sin querer, el usuario
  // leeria un boton que no existe en su pantalla.
  assert.equal(Confirmacion.avisoCaducada("archivo"), Confirmacion.AVISO_CADUCADA);
  assert.equal(Confirmacion.avisoCaducada(undefined), Confirmacion.AVISO_CADUCADA);
});
