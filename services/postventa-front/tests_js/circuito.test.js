// services/postventa-front/tests_js/circuito.test.js
// F-025 · El circuito de UN parte: archivar, adjuntar y cerrar del tirón.
//
// Este fichero existe por un defecto concreto y documentado. Hasta F-025 el
// encadenado «adjuntar y luego cerrar» vivía en `js/app.js`, que no ejecuta
// ningún test: F-019 ya demostró una vez que allí se puede borrar una línea de
// orden y dejar los tests en verde. Lo que F-025 mudaría a `app.js` sería el
// orden de **tres escrituras, dos de ellas en un ERP de producción**, así que
// el circuito se muda a `js/pipeline.js` y se prueba aquí.
//
// Lo que se comprueba no es «que funcione»: es el ORDEN, el NÚMERO de llamadas
// y que ninguna de las dos que tocan el ERP sale sin `commit` y `confirmado`.
// Con la confirmación única, no hay ninguna pantalla intermedia que lo mire.
//
// TODOS los valores están INVENTADOS: el código de obra, el de incidencia, el
// `oid` y el correo, cuyo dominio no existe. Los partes de verdad llevan DNI y
// observaciones manuscritas de clientes y no entran en el repositorio.

const test = require("node:test");
const assert = require("node:assert/strict");

const {
  pendientesDeCircuito,
  porcentajeDeTanda,
  ejecutarCircuito,
  conGuardaDeTanda,
  hayTandaEnCurso,
} = require("../js/pipeline.js");

const HASH = "a1b2c3d4e5f6";
const OID = "oid-inventado-para-el-test";
const CORREO = "fulanito@ejemplo.invalido";
const INCIDENCIA = "XX00.00 - 0000";
const CODIGO_EN_SIGRID = "XX00.00/0000";

/** Un `FormData` de mentira que recuerda lo que le metieron, en orden. */
class FormDataFalso {
  constructor() {
    this.campos = [];
  }
  append(nombre, valor, nombreFichero) {
    this.campos.push({ nombre, valor, nombreFichero });
  }
  get(nombre) {
    const encontrado = this.campos.find((campo) => campo.nombre === nombre);
    return encontrado ? encontrado.valor : null;
  }
  tiene(nombre) {
    return this.campos.some((campo) => campo.nombre === nombre);
  }
}

/** Lo que responden los tres endpoints cuando todo va bien. */
const RESPUESTA_OK = {
  archivar: {
    nombre_fichero: "0000 XX00.00 - 0000.pdf",
    carpeta: "Inventada/2026",
    estado: "archivado",
    web_url: "https://ejemplo.invalido/inventado.pdf",
  },
  adjuntar: { estado: "adjuntado", numero_incidencia: CODIGO_EN_SIGRID },
  cerrar: { estado: "cerrado", numero_incidencia: CODIGO_EN_SIGRID },
};

/**
 * Un `api` de mentira que **graba todas las llamadas en orden**.
 *
 * El guion se escribe por paso: un valor es la respuesta, y `{fallo: X}`
 * rechaza con `X`. Es lo único con lo que se puede comprobar que un fallo en
 * el paso 1 deja el paso 2 y el 3 **sin ejecutar**, que es R17 y R18.
 */
function apiDoble(guion) {
  const preparado = guion || {};
  const llamadas = [];

  function responder(paso, cuerpo, hash) {
    llamadas.push({ paso: paso, cuerpo: cuerpo, hash: hash });
    const respuesta = Object.prototype.hasOwnProperty.call(preparado, paso)
      ? preparado[paso]
      : RESPUESTA_OK[paso];
    if (respuesta && respuesta.fallo) {
      return Promise.reject(respuesta.fallo);
    }
    return Promise.resolve(respuesta);
  }

  return {
    llamadas: llamadas,
    pasos: function () {
      return llamadas.map((llamada) => llamada.paso);
    },
    cuerpoDe: function (paso) {
      const encontrada = llamadas.find((llamada) => llamada.paso === paso);
      return encontrada ? encontrada.cuerpo : null;
    },
    archivar: function (cuerpo, hash) {
      return responder("archivar", cuerpo, hash);
    },
    adjuntar: function (cuerpo, hash) {
      return responder("adjuntar", cuerpo, hash);
    },
    cerrar: function (cuerpo, hash) {
      return responder("cerrar", cuerpo, hash);
    },
  };
}

/** Un parte apto, guardado y con su PDF: el que entra en la tanda. */
function parteDeLaTanda(sobrescribir) {
  return Object.assign(
    {
      hash: HASH,
      guardado: true,
      archivado: false,
      cerrado: false,
      grafico: "",
      fichero: { name: "parte-a1b2c3d4.pdf" },
      validacion: { veredicto: "apto", destino: "archivo_y_cierre" },
      extraccion: {
        campos: {
          codigo_obra: { valor: "0000", confianza_pct: 98 },
          numero_incidencia: { valor: INCIDENCIA, confianza_pct: 96 },
        },
      },
    },
    sobrescribir || {},
  );
}

/** `ejecutarCircuito` con lo mínimo para que no toque ni red ni `FormData`. */
function correr(parte, api, opciones) {
  return ejecutarCircuito(
    parte,
    api,
    Object.assign(
      {
        usuarioOid: OID,
        correo: CORREO,
        FabricaFormData: FormDataFalso,
      },
      opciones || {},
    ),
  );
}

/** Un error de la puerta de entorno, como el que compone `js/api.js` ante un 503. */
function errorDeEntorno() {
  return {
    tipo: "entorno",
    http: 503,
    mensaje: "Este entorno no escribe: la puerta de entorno está apagada.",
  };
}

/** Un error de este parte y solo de este parte, como un 409. */
function errorDelParte(mensaje) {
  return { tipo: "no_apto", http: 409, mensaje: mensaje };
}

// ==========================================================================
// T3 · R24 · Un solo selector, y lleva lo que quedó a medias
// ==========================================================================

test("R24 · la tanda lleva los partes que aún no se han archivado", () => {
  const parte = parteDeLaTanda();
  assert.deepEqual(pendientesDeCircuito([parte]), [parte]);
});

test("R24 · la tanda lleva los archivados SIN adjuntar", () => {
  // Es el agujero que R24 cierra: con el selector viejo (`archivables()`), un
  // parte archivado caía fuera de la tanda y, al desaparecer el botón de
  // cerrar, no había forma de recuperarlo.
  const parte = parteDeLaTanda({ archivado: true });
  assert.deepEqual(pendientesDeCircuito([parte]), [parte]);
});

test("R24 · la tanda lleva los adjuntados SIN cerrar", () => {
  const parte = parteDeLaTanda({ archivado: true, grafico: "adjuntado" });
  assert.deepEqual(pendientesDeCircuito([parte]), [parte]);
});

test("R24 · los ya cerrados quedan fuera", () => {
  const parte = parteDeLaTanda({
    archivado: true,
    grafico: "adjuntado",
    cerrado: true,
  });
  assert.deepEqual(pendientesDeCircuito([parte]), []);
});

test("R36 · los que no son aptos quedan fuera, aunque estén guardados", () => {
  const revision = parteDeLaTanda({
    validacion: { veredicto: "no_apto", destino: "revision_manual" },
  });
  const cola = parteDeLaTanda({
    validacion: { veredicto: "apto", destino: "cola_validacion_humana" },
  });
  const sinVeredicto = parteDeLaTanda({ validacion: null });

  assert.deepEqual(pendientesDeCircuito([revision, cola, sinVeredicto]), []);
});

test("R24 · los que no se pudieron guardar quedan fuera", () => {
  // El backend respondería 409 y no subiría nada: ofrecerlo sería prometer
  // algo que va a fallar con el usuario delante.
  const parte = parteDeLaTanda({ guardado: false });
  assert.deepEqual(pendientesDeCircuito([parte]), []);
});

test("R24 · una lista vacía o ausente no revienta", () => {
  assert.deepEqual(pendientesDeCircuito([]), []);
  assert.deepEqual(pendientesDeCircuito(null), []);
});

// ==========================================================================
// T3 · R12 · El porcentaje es de LA TANDA, no de la remesa
// ==========================================================================

test("R12 · el porcentaje se calcula sobre el tamaño de la tanda", () => {
  // El denominador viejo era `partes.length`: archivar 4 partes de una remesa
  // de 22 enseñaba un 18 % al terminar, que es mentira sobre lo que se pidió.
  assert.equal(porcentajeDeTanda(4, 4), 100);
  assert.equal(porcentajeDeTanda(2, 4), 50);
  assert.equal(porcentajeDeTanda(1, 3), 33);
  assert.equal(porcentajeDeTanda(0, 4), 0);
});

test("R12 · con la tanda vacía el porcentaje es 0 y no NaN", () => {
  assert.equal(porcentajeDeTanda(0, 0), 0);
  assert.equal(porcentajeDeTanda(3, 0), 0);
});

// ==========================================================================
// T4 · R7, R8, R9, R13 · El circuito, su orden y su número de llamadas
// ==========================================================================

test("R7 · el orden es archivar → adjuntar → cerrar", async () => {
  const api = apiDoble();

  const resultado = await correr(parteDeLaTanda(), api);

  assert.deepEqual(api.pasos(), ["archivar", "adjuntar", "cerrar"]);
  assert.equal(resultado.estado, "cerrado");
  assert.equal(resultado.tipoError, "");
});

test("R9 · son TRES llamadas por parte y ni una más", async () => {
  // Con la confirmación única desaparecen las dos llamadas de cálculo previo:
  // de cinco peticiones por parte se pasa a tres. Si alguien repusiera el
  // dry-run por separado, este número se iría a cinco y el test lo diría.
  const api = apiDoble();

  await correr(parteDeLaTanda(), api);

  assert.equal(api.llamadas.length, 3);
});

test("R8 · adjuntar se pide SIEMPRE con commit y confirmado", async () => {
  const api = apiDoble();

  await correr(parteDeLaTanda(), api);

  const cuerpo = api.cuerpoDe("adjuntar");
  assert.equal(cuerpo.get("commit"), "true");
  assert.equal(cuerpo.get("confirmado"), "true");
});

test("R8 · cerrar se pide SIEMPRE con commit y confirmado", async () => {
  const api = apiDoble();

  await correr(parteDeLaTanda(), api);

  const cuerpo = api.cuerpoDe("cerrar");
  assert.equal(cuerpo.commit, true);
  assert.equal(cuerpo.confirmado, true);
});

test("R8 · ninguna llamada al ERP sale sin commit", async () => {
  // El control negativo de R5: ya no existe ningún camino que pida el cálculo
  // previo por separado, así que una llamada sin `commit` sería una pantalla
  // que alguien repuso sin querer.
  const api = apiDoble();

  await correr(parteDeLaTanda(), api);

  api.llamadas.forEach((llamada) => {
    if (llamada.paso === "adjuntar") {
      assert.ok(llamada.cuerpo.tiene("commit"), "adjuntar sin commit");
    }
    if (llamada.paso === "cerrar") {
      assert.equal(llamada.cuerpo.commit, true, "cerrar sin commit");
    }
  });
});

test("R7 · las tres llamadas van con el hash del parte", async () => {
  const api = apiDoble();

  await correr(parteDeLaTanda(), api);

  api.llamadas.forEach((llamada) => assert.equal(llamada.hash, HASH));
});

test("R13 · alPaso publica archivando, adjuntando y cerrando, en ese orden", async () => {
  // Es lo que distingue «está trabajando» de «se ha colgado». Con la cola a
  // tres, el usuario ve tres líneas moviéndose durante los ~20 s que tarda
  // cada parte, y por eso no vuelve a pulsar el botón.
  const pasos = [];
  const api = apiDoble();

  await correr(parteDeLaTanda(), api, {
    alPaso: (paso) => pasos.push(paso),
  });

  assert.deepEqual(pasos, ["archivando", "adjuntando", "cerrando"]);
});

test("R25 · un parte ya archivado no se vuelve a subir a SharePoint", async () => {
  const api = apiDoble();
  const pasos = [];

  const resultado = await correr(
    parteDeLaTanda({ archivado: true }),
    api,
    { alPaso: (paso) => pasos.push(paso) },
  );

  assert.deepEqual(api.pasos(), ["adjuntar", "cerrar"]);
  assert.deepEqual(pasos, ["adjuntando", "cerrando"]);
  assert.equal(resultado.estado, "cerrado");
});

test("R26 · un parte ya adjuntado no vuelve a mandar los bytes a la pasarela", async () => {
  const api = apiDoble();

  const resultado = await correr(
    parteDeLaTanda({ grafico: "adjuntado" }),
    api,
  );

  assert.deepEqual(api.pasos(), ["archivar", "cerrar"]);
  assert.equal(resultado.estado, "cerrado");
});

test("R25, R26 · un parte archivado y adjuntado solo pide el cierre", async () => {
  const api = apiDoble();

  await correr(
    parteDeLaTanda({ archivado: true, grafico: "adjuntado" }),
    api,
  );

  assert.deepEqual(api.pasos(), ["cerrar"]);
});

// ==========================================================================
// T5 · R17-R19, R27, R37 · Qué pasa si falla a mitad
// ==========================================================================

test("R17 · si falla el archivo no se adjunta ni se cierra", async () => {
  const api = apiDoble({ archivar: { fallo: errorDelParte("no cabe") } });

  const resultado = await correr(parteDeLaTanda(), api);

  assert.deepEqual(api.pasos(), ["archivar"]);
  assert.equal(resultado.estado, "error_archivo");
  assert.equal(resultado.paso, "archivar");
  assert.equal(resultado.tipoError, "parte");
  assert.ok(resultado.error.includes("no cabe"));
});

test("R18 · si falla el adjuntado no se cierra nada", async () => {
  // La mitad de front de la garantía: ninguna reclamación queda cerrada sin su
  // parte dentro del ERP. La otra mitad la pone el backend, que responde 409
  // sin tocar Sigrid, y sigue ahí (F-025 R34).
  const api = apiDoble({ adjuntar: { fallo: errorDelParte("la pasarela dice que no") } });

  const resultado = await correr(parteDeLaTanda(), api);

  assert.deepEqual(api.pasos(), ["archivar", "adjuntar"]);
  assert.equal(resultado.estado, "error_grafico");
  assert.equal(resultado.paso, "adjuntar");
  assert.equal(resultado.cerrado, false);
});

test("R27 · si la reclamación ya estaba cerrada no se cierra, y no es un error", async () => {
  const api = apiDoble({
    adjuntar: { estado: "ya_cerrada", numero_incidencia: CODIGO_EN_SIGRID },
  });

  const resultado = await correr(parteDeLaTanda(), api);

  assert.deepEqual(api.pasos(), ["archivar", "adjuntar"]);
  assert.equal(resultado.estado, "ya_cerrada");
  assert.equal(resultado.tipoError, "");
  assert.equal(resultado.error, "");
  // Sale de la tanda: si volviera a entrar, el reintento la pediría otra vez.
  assert.equal(resultado.cerrado, true);
  assert.ok(resultado.mensaje.includes("ya_cerrada"));
});

test("R19 · si falla el cierre con el gráfico dentro, el estado es adjuntado", async () => {
  // Es el estado «adjuntado pero no cerrado», que tiene salida propia en
  // pantalla: el recuadro ámbar con «Reintentar el cierre» (R65 de F-012).
  // Decir `error_cierre` a secas escondería que el parte YA está en Sigrid.
  const api = apiDoble({ cerrar: { fallo: errorDelParte("el ERP ha dicho que no") } });

  const resultado = await correr(parteDeLaTanda(), api);

  assert.deepEqual(api.pasos(), ["archivar", "adjuntar", "cerrar"]);
  assert.equal(resultado.estado, "adjuntado");
  assert.equal(resultado.grafico, "adjuntado");
  assert.equal(resultado.cerrado, false);
  assert.equal(resultado.tipoError, "parte");
  assert.ok(resultado.error.includes("el ERP ha dicho que no"));
});

test("R20 · el circuito NUNCA lanza: un parte roto no tumba la tanda", async () => {
  const api = apiDoble({ archivar: { fallo: new Error("reventón inventado") } });

  const resultado = await correr(parteDeLaTanda(), api);

  assert.equal(resultado.estado, "error_archivo");
  assert.ok(resultado.error.includes("reventón inventado"));
});

test("R36 · un parte no apto no llega a ninguna petición", async () => {
  // `cuerpoDeArchivo` se niega a componer nada que no sea apto, y aquí se
  // comprueba que esa negativa se convierte en un resultado y no en una
  // excepción que tumbe la tanda.
  const api = apiDoble();

  const resultado = await correr(
    parteDeLaTanda({
      validacion: { veredicto: "no_apto", destino: "revision_manual" },
    }),
    api,
  );

  assert.deepEqual(api.pasos(), []);
  assert.equal(resultado.estado, "error_archivo");
});

test("R37 · el resultado trae el número de incidencia que devolvió el backend", async () => {
  // No es cosmético: al no haber pantalla previa, el resumen es la primera y
  // única ocasión en que quien pulsó puede ver sobre qué reclamación se
  // escribió.
  const api = apiDoble();

  const resultado = await correr(parteDeLaTanda(), api);

  assert.equal(resultado.numeroIncidencia, CODIGO_EN_SIGRID);
});

test("R37 · el número de incidencia sobrevive a un cierre fallido", async () => {
  const api = apiDoble({ cerrar: { fallo: errorDelParte("no se pudo") } });

  const resultado = await correr(parteDeLaTanda(), api);

  assert.equal(resultado.numeroIncidencia, CODIGO_EN_SIGRID);
});

test("R37 · con los tres pasos en verde y sin número en la respuesta, no se inventa ninguno", async () => {
  // ESTE es el control negativo de R37, y es el que faltaba hasta la review.
  //
  // Es el único guion del fichero que ejecuta `numeroDeIncidenciaDe` con la
  // clave AUSENTE: el circuito entero en verde —los tres pasos ejecutados— y
  // un backend que responde con éxito pero sin `numero_incidencia`. Los demás
  // tests de R37 o traen la clave, o fallan antes de llegar a la función.
  //
  // Sin él, `numeroDeIncidenciaDe` se puede cambiar para rellenar el hueco con
  // el número LEÍDO DEL PAPEL y ningún test cae. Y ese es justo el número que
  // §0 de `requirements.md` acepta que pueda estar mal leído: enseñarlo como
  // si lo hubiera dicho el ERP no compensa ese riesgo, lo disfraza. El resumen
  // es la única ocasión de detectar que se escribió sobre otra reclamación.
  const api = apiDoble({
    adjuntar: { estado: "adjuntado" },
    cerrar: { estado: "cerrado" },
  });

  const resultado = await correr(parteDeLaTanda(), api);

  assert.deepEqual(api.pasos(), ["archivar", "adjuntar", "cerrar"]);
  assert.equal(resultado.cerrado, true, "el circuito tiene que haber llegado al final");
  assert.equal(resultado.numeroIncidencia, "");
  assert.notEqual(
    resultado.numeroIncidencia,
    INCIDENCIA,
    "el número del papel no puede colarse como si lo hubiera dicho el ERP",
  );
  assert.ok(
    !resultado.mensaje.includes(INCIDENCIA) &&
      !resultado.mensaje.includes(CODIGO_EN_SIGRID),
    "tampoco por la puerta de atrás del mensaje del resumen",
  );
});

test("R37 · si solo lo devuelve el cierre, ese es el que se enseña", async () => {
  // La misma función, con la clave ausente en un paso y presente en el otro:
  // el hueco del paso 2 no se rellena con nada inventado y el paso 3 lo pone.
  const api = apiDoble({ adjuntar: { estado: "adjuntado" } });

  const resultado = await correr(parteDeLaTanda(), api);

  assert.equal(resultado.numeroIncidencia, CODIGO_EN_SIGRID);
});

test("R37 · un parte que no llega al ERP se queda sin número", async () => {
  // Ojo con lo que prueba este test, que no es lo que parece: al fallar el
  // paso 1 el circuito se corta y `numeroDeIncidenciaDe` **no se ejecuta**.
  // Lo que fija es que el campo nace vacío y nadie lo rellena por el camino
  // del error. El control negativo de la función es el test de arriba.
  const api = apiDoble({ archivar: { fallo: errorDelParte("no cabe") } });

  const resultado = await correr(parteDeLaTanda(), api);

  assert.equal(resultado.estado, "error_archivo");
  assert.equal(resultado.numeroIncidencia, "");
});

test("R16 · el resultado dice hasta dónde llegó el parte", async () => {
  const api = apiDoble();

  const resultado = await correr(parteDeLaTanda(), api);

  assert.equal(resultado.archivado, true);
  assert.equal(resultado.grafico, "adjuntado");
  assert.equal(resultado.cerrado, true);
  assert.equal(resultado.paso, "cerrar");
  assert.ok(resultado.archivo.web_url.length > 0);
});

// ==========================================================================
// T6 · R21, R22 · La puerta de entorno, que son DOS ventanas distintas
// ==========================================================================

test("R21 · con la ventana del ERP cerrada se archiva y no se pide el ERP", async () => {
  // La ventana no se va a abrir a mitad de tanda, y veinte partes por dos
  // llamadas de 503 garantizado es ruido. Pero el archivo SÍ sirve: deja el
  // documento guardado y el parte listo para la tanda siguiente.
  const api = apiDoble();

  const resultado = await correr(parteDeLaTanda(), api, { erpCerrado: true });

  assert.deepEqual(api.pasos(), ["archivar"]);
  assert.equal(resultado.estado, "archivado");
  assert.equal(resultado.archivado, true);
  assert.equal(resultado.tipoError, "");
});

test("R22 · un 503 al adjuntar es de entorno y su ámbito es el ERP", async () => {
  const api = apiDoble({ adjuntar: { fallo: errorDeEntorno() } });

  const resultado = await correr(parteDeLaTanda(), api);

  assert.equal(resultado.tipoError, "entorno");
  assert.equal(resultado.ambito, "erp");
  assert.deepEqual(api.pasos(), ["archivar", "adjuntar"]);
});

test("R22 · un 503 al cerrar es de entorno y su ámbito es el ERP", async () => {
  const api = apiDoble({ cerrar: { fallo: errorDeEntorno() } });

  const resultado = await correr(parteDeLaTanda(), api);

  assert.equal(resultado.tipoError, "entorno");
  assert.equal(resultado.ambito, "erp");
  // El gráfico SÍ entró: el parte queda adjuntado, no en error.
  assert.equal(resultado.estado, "adjuntado");
});

test("R22 · un 503 al archivar es de entorno y su ámbito es el archivo", async () => {
  // Son dos ventanas distintas —`ARCHIVO_HABILITADO` y `CIERRE_HABILITADO`— y
  // se tratan distinto: sin archivo no hay nada que adjuntar ni que cerrar, y
  // la tanda se detiene.
  const api = apiDoble({ archivar: { fallo: errorDeEntorno() } });

  const resultado = await correr(parteDeLaTanda(), api);

  assert.equal(resultado.tipoError, "entorno");
  assert.equal(resultado.ambito, "archivo");
  assert.deepEqual(api.pasos(), ["archivar"]);
});

test("R22 · un error que no es de entorno no levanta ninguna bandera", async () => {
  const api = apiDoble({ adjuntar: { fallo: errorDelParte("este parte, no el sistema") } });

  const resultado = await correr(parteDeLaTanda(), api);

  assert.equal(resultado.tipoError, "parte");
  assert.equal(resultado.ambito, "");
});

// ==========================================================================
// T6 · R14 · La guarda de reentrada
// ==========================================================================

test("R14 · con una tanda en curso, la segunda no arranca", async () => {
  // Hoy la única defensa contra la doble pulsación es el `:disabled` del HTML,
  // que ningún test ejecuta. Detrás hay tres escrituras, dos en un ERP de
  // producción.
  let soltar;
  const enVuelo = new Promise((resolver) => {
    soltar = resolver;
  });
  let arrancadas = 0;

  const primera = conGuardaDeTanda(async () => {
    arrancadas += 1;
    await enVuelo;
    return "la primera";
  });

  const segunda = await conGuardaDeTanda(async () => {
    arrancadas += 1;
    return "la segunda";
  });

  assert.equal(segunda.arrancada, false);
  assert.equal(arrancadas, 1);

  soltar();
  const resultado = await primera;
  assert.equal(resultado.arrancada, true);
  assert.equal(resultado.valor, "la primera");
});

test("R14 · al terminar la tanda, la siguiente sí arranca", async () => {
  const primera = await conGuardaDeTanda(async () => "una");
  const segunda = await conGuardaDeTanda(async () => "otra");

  assert.equal(primera.arrancada, true);
  assert.equal(segunda.arrancada, true);
  assert.equal(segunda.valor, "otra");
});

test("R14 · una tanda que revienta también suelta la guarda", async () => {
  // Sin esto, un fallo inesperado dejaría la pantalla bloqueada para siempre y
  // la única salida sería recargar.
  await assert.rejects(
    conGuardaDeTanda(async () => {
      throw new Error("reventón inventado");
    }),
  );

  assert.equal(hayTandaEnCurso(), false);
  const despues = await conGuardaDeTanda(async () => "sigue viva");
  assert.equal(despues.arrancada, true);
});
