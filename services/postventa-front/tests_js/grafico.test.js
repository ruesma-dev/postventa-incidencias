// services/postventa-front/tests_js/grafico.test.js
// F-012 · Lo que el front decide antes de adjuntar el parte al ERP.
//
// TODOS los valores de este fichero están INVENTADOS: el código de obra, el de
// incidencia, el `oid` y el correo, cuyo dominio no existe. Los partes de
// verdad llevan DNI y observaciones manuscritas de clientes y no entran en el
// repositorio.
//
// Va aparte de `cierre.test.js` por lo mismo que aquel fue aparte de
// `pipeline.test.js`: un fallo aquí dice de qué feature es. Y lo que hay
// detrás de estas dos funciones no es un cambio de estado: es **el PDF del
// parte** viajando hasta un ERP de producción.

const test = require("node:test");
const assert = require("node:assert/strict");

const {
  cuerpoDeGrafico,
  estaAdjuntado,
  esCerrable,
} = require("../js/pipeline.js");

const HASH = "a1b2c3d4e5f6";
const OID = "oid-inventado-para-el-test";
const CORREO = "fulanito@ejemplo.invalido";

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
  get nombres() {
    return this.campos.map((campo) => campo.nombre);
  }
}

/** Un parte aprobado, guardado, archivado y con su PDF: el que sí se adjunta.
 *
 * Enmienda del 2026-09-16 · F-028 T17: el fixture gana `estadoParte`, el
 * bloque `estado` que devuelve el backend. Desde F-028 lo que abre el circuito
 * es el estado del parte y no el veredicto (R33).
 */
function parteAdjuntable(sobrescribir) {
  return Object.assign(
    {
      hash: HASH,
      guardado: true,
      archivado: true,
      estadoParte: { estado: "aprobado", decidido_por_persona: false },
      fichero: { name: "parte-a1b2c3d4.pdf" },
      validacion: { veredicto: "apto", destino: "archivo_y_cierre" },
      extraccion: {
        campos: {
          codigo_obra: { valor: "0000", confianza_pct: 98 },
          numero_incidencia: { valor: "XX00.00 - 0000", confianza_pct: 96 },
          dni_cliente: { valor: "00000000T", confianza_pct: 91 },
          observaciones: { valor: "Texto manuscrito inventado", confianza_pct: 80 },
          nombre_propietario: { valor: "Nombreinventado", confianza_pct: 90 },
        },
      },
    },
    sobrescribir || {},
  );
}

function componer(parte, opciones) {
  return cuerpoDeGrafico(
    parte,
    Object.assign({ usuarioOid: OID }, opciones || {}),
    FormDataFalso,
  );
}

// --- Las precondiciones: lo mismo que el cierre ----------------------------

test("f012: un parte apto, archivado y con PDF compone su multipart", () => {
  const cuerpo = componer(parteAdjuntable());

  assert.equal(cuerpo.get("hash"), HASH);
  assert.equal(cuerpo.get("codigo_obra"), "0000");
  assert.equal(cuerpo.get("numero_incidencia"), "XX00.00 - 0000");
  assert.equal(cuerpo.get("veredicto"), "apto");
  assert.equal(cuerpo.get("destino"), "archivo_y_cierre");
  assert.equal(cuerpo.get("estado_archivo"), "archivado");
  assert.equal(cuerpo.get("usuario_oid"), OID);
});

test("f012 R14 / f028 R33: un parte que no consta APROBADO no compone nada", () => {
  // No basta con no pintar el botón: aunque se pulse dos veces, aquí se para.
  //
  // Enmienda del 2026-09-16 · F-028 T17: antes se montaba con un veredicto
  // `no_apto`, porque el veredicto era el criterio. Ahora el criterio es el
  // estado, y por eso se prueban los tres que no son `aprobado` —incluido
  // `rechazado`, que antes no se podía ni montar—.
  for (const estado of ["pendiente", "rechazado", "cerrado"]) {
    assert.throws(
      () =>
        componer(
          parteAdjuntable({
            estadoParte: { estado: estado, decidido_por_persona: true },
          }),
        ),
      /no se puede adjuntar/,
      estado,
    );
  }
});

test("f012 R15: un parte que no consta archivado no compone nada", () => {
  // Lo que se sube al ERP son EXACTAMENTE los bytes que se archivaron. Si el
  // archivo no consta, no hay nada con lo que cotejar después lo que quedó
  // dentro de Sigrid.
  assert.throws(
    () => componer(parteAdjuntable({ archivado: false })),
    /no se puede adjuntar/,
  );
});

test("f012: un parte sin número de incidencia no compone nada", () => {
  const sinIncidencia = parteAdjuntable();
  sinIncidencia.extraccion.campos.numero_incidencia = {
    valor: null,
    confianza_pct: 0,
  };

  assert.throws(() => componer(sinIncidencia), /no se puede adjuntar/);
});

test("f012: un parte sin su PDF no compone nada, y lo dice", () => {
  // Es el caso propio de esta feature: el cierre no necesita el fichero y este
  // sí. Un `FormData` sin fichero produciría un 400 del backend con el usuario
  // delante.
  assert.throws(
    () => componer(parteAdjuntable({ fichero: null })),
    /no trae su PDF/,
  );
});

test("f012 R12: sin identidad no se compone nada", () => {
  assert.throws(
    () => cuerpoDeGrafico(parteAdjuntable(), {}, FormDataFalso),
    /no se sabe quién pide el gráfico/,
  );
});

// --- El fichero va, y los campos manuscritos NO ----------------------------

test("f012 R6: el multipart lleva el fichero, que es lo que lo distingue", () => {
  const cuerpo = componer(parteAdjuntable());
  const fichero = cuerpo.campos.find((campo) => campo.nombre === "fichero");

  assert.ok(fichero, "el multipart tiene que llevar el PDF");
  assert.equal(fichero.nombreFichero, "parte-a1b2c3d4.pdf");
});

test("f012 R53: el multipart no lleva NINGÚN campo manuscrito", () => {
  // El DNI y las observaciones del cliente no viajan otra vez: van dentro del
  // PDF, que es donde tienen que estar. Mandarlos aparte dobla la exposición
  // de un dato personal directo a cambio de nada.
  const cuerpo = componer(parteAdjuntable());

  for (const prohibido of ["dni_cliente", "observaciones", "nombre_propietario"]) {
    assert.equal(cuerpo.tiene(prohibido), false, `no puede ir ${prohibido}`);
  }
  const texto = JSON.stringify(cuerpo.campos);
  assert.equal(texto.includes("00000000T"), false);
  assert.equal(texto.includes("Texto manuscrito inventado"), false);
});

test("f012: el multipart lleva ocho campos y el fichero, ni uno más", () => {
  // Uno de más es uno que nadie ha revisado, y por aquí pasa el ERP.
  const cuerpo = componer(parteAdjuntable());

  assert.deepEqual(cuerpo.nombres.sort(), [
    "codigo_obra",
    "destino",
    "estado_archivo",
    "fichero",
    "hash",
    "numero_incidencia",
    "usuario_oid",
    "veredicto",
  ]);
});

// --- El dry-run es lo que se hace por omisión ------------------------------

test("f012 R57: sin pedirlo, el cuerpo NO lleva commit ni confirmado", () => {
  // Quien componga este cuerpo sin pensar no escribe nada en el ERP.
  const cuerpo = componer(parteAdjuntable());

  assert.equal(cuerpo.tiene("commit"), false);
  assert.equal(cuerpo.tiene("confirmado"), false);
});

test("f012 R57: commit y confirmado viajan como la cadena 'true'", () => {
  // El backend solo acepta EXACTAMENTE esa cadena: en un multipart todo llega
  // como texto, y en Python `"false"` es verdadero.
  const cuerpo = componer(parteAdjuntable(), {
    commit: true,
    confirmado: true,
  });

  assert.equal(cuerpo.get("commit"), "true");
  assert.equal(cuerpo.get("confirmado"), "true");
});

test("f012 R57: un commit que no es exactamente true no se pone", () => {
  for (const valor of ["true", 1, "si", {}]) {
    const cuerpo = componer(parteAdjuntable(), { commit: valor });
    assert.equal(cuerpo.tiene("commit"), false, `«${valor}» ha puesto commit`);
  }
});

test("f012: el correo solo viaja si lo hay", () => {
  // Hace falta la primera vez de cada persona, para derivar el login candidato
  // que el ERP tendrá que confirmar. Quien ya tiene su correspondencia
  // guardada no lo necesita.
  assert.equal(componer(parteAdjuntable()).tiene("correo"), false);
  assert.equal(
    componer(parteAdjuntable(), { correo: CORREO }).get("correo"),
    CORREO,
  );
});

// --- R64 · la decisión que impide cerrar sin gráfico -----------------------

test("f012 R64: solo cuenta como adjuntado lo que el BACKEND dijo", () => {
  // La decisión vive aquí, y no en `app.js`, para que tenga test. Y lo que se
  // mira es el estado que devolvió el backend: deducirlo en el navegador sería
  // afirmar que un parte está dentro de Sigrid mirando una variable local.
  assert.equal(estaAdjuntado({ grafico: "adjuntado" }), true);
});

test("f012 R64: ningún otro estado cuenta como adjuntado", () => {
  // `dry_run_ok` es el más peligroso: significa «se miró qué pasaría», no «el
  // parte está dentro». Aceptarlo pediría el cierre de una reclamación cuyo
  // gráfico no se ha escrito, que es la anomalía que la feature elimina.
  for (const estado of [
    "dry_run_ok",
    "error",
    "pendiente",
    "ya_cerrada",
    undefined,
    null,
    "",
  ]) {
    assert.equal(
      estaAdjuntado({ grafico: estado }),
      false,
      `«${estado}» no puede contar como adjuntado`,
    );
  }
});

test("f012 R64: un parte sin nada tampoco está adjuntado", () => {
  assert.equal(estaAdjuntado(null), false);
  assert.equal(estaAdjuntado(undefined), false);
  assert.equal(estaAdjuntado({}), false);
});

test("f012: adjuntable y cerrable son la misma puerta, y eso es deliberado", () => {
  // Solo se adjunta lo que se va a poder cerrar (R16, R17): el gráfico es la
  // primera mitad del cierre y no se deja en el ERP sin la segunda.
  const parte = parteAdjuntable();

  assert.equal(esCerrable(parte), true);
  assert.doesNotThrow(() => componer(parte));

  // Enmienda del 2026-09-16 · F-028 T17: el que se queda fuera de las dos es
  // el que no consta aprobado, no el que no es apto.
  const rechazado = parteAdjuntable({
    estadoParte: { estado: "rechazado", decidido_por_persona: true },
  });
  assert.equal(esCerrable(rechazado), false);
  assert.throws(() => componer(rechazado));
});
