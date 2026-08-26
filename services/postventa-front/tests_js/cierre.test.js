// services/postventa-front/tests_js/cierre.test.js
// F-009 · Lo que el front decide antes de pedir un cierre en Sigrid.
//
// TODOS los valores de este fichero están INVENTADOS: `RS26.08/0123`, el `oid`
// y el correo, cuyo dominio no existe. Los partes de verdad llevan DNI y
// observaciones manuscritas de clientes y no entran en el repositorio.
//
// Va aparte de `pipeline.test.js` a propósito, por lo mismo que
// `test_f009_arquitectura.py` va aparte del de F-006: un fallo aquí dice de
// qué feature es. Y lo que hay detrás de estas dos funciones no es una subida
// de ficheros: es la única escritura de este proyecto en el ERP de producción.

const test = require("node:test");
const assert = require("node:assert/strict");

const { cuerpoDeCierre, esCerrable } = require("../js/pipeline.js");

const HASH = "a1b2c3d4e5f6";
const OID = "oid-inventado-para-el-test";
const CORREO = "fulanito@ejemplo.invalido";

/** Un parte apto, guardado y ya archivado. El caso que sí se cierra. */
function parteCerrable(sobrescribir) {
  return Object.assign(
    {
      hash: HASH,
      guardado: true,
      archivado: true,
      validacion: { veredicto: "apto", destino: "archivo_y_cierre" },
      extraccion: {
        campos: {
          numero_incidencia: { valor: "RS26.08 - 0123", confianza_pct: 96 },
          dni_cliente: { valor: "00000000T", confianza_pct: 91 },
          observaciones: { valor: "Texto manuscrito inventado", confianza_pct: 80 },
        },
      },
    },
    sobrescribir || {},
  );
}

// --- Las DOS precondiciones propias, y ninguna más -------------------------

test("f009: un parte apto y archivado sí es cerrable", () => {
  assert.equal(esCerrable(parteCerrable()), true);
});

test("f009 R17: un parte que no consta archivado NO es cerrable", () => {
  // Primero el documento, después el cierre. Si el PDF no está guardado en
  // ninguna parte, cerrar la incidencia la da por resuelta sin dejar la prueba.
  assert.equal(esCerrable(parteCerrable({ archivado: false })), false);
});

test("f009 R16: un parte no apto NO es cerrable aunque esté archivado", () => {
  const noApto = parteCerrable({
    validacion: { veredicto: "no_apto", destino: "cola_validacion_humana" },
  });

  assert.equal(esCerrable(noApto), false);
});

test("f009: sin número de incidencia no hay nada que cerrar", () => {
  // Es lo que identifica la reclamación en el ERP: sin él no hay a quién
  // preguntar, y el backend responde 400.
  const sinCodigo = parteCerrable();
  sinCodigo.extraccion.campos.numero_incidencia = { valor: null, confianza_pct: 0 };

  assert.equal(esCerrable(sinCodigo), false);
});

test("f009: la corrección de una persona manda sobre lo que leyó la IA", () => {
  // Si alguien arregló el número de incidencia en pantalla, es ESE el que
  // tiene que viajar al ERP. Cerrar con el que leyó mal la IA cerraría otra
  // incidencia.
  const corregido = parteCerrable({ ediciones: { numero_incidencia: "RS26.08/0999" } });

  assert.equal(
    cuerpoDeCierre(corregido, { usuarioOid: OID }).numero_incidencia,
    "RS26.08/0999",
  );
});

// --- El cuerpo: qué viaja y qué no -----------------------------------------

test("f009 R8: por omisión el cuerpo es un dry-run y NO pide commit", () => {
  const cuerpo = cuerpoDeCierre(parteCerrable(), { usuarioOid: OID });

  assert.equal(cuerpo.commit, undefined);
  assert.equal(cuerpo.confirmado, undefined);
});

test("f009 R12: commit y confirmado solo se ponen si se piden, y solo con true", () => {
  // Se compara con `=== true` en el módulo: una cadena "false" es verdadera en
  // JavaScript, y aquí eso significaría escribir en el ERP de producción
  // porque alguien pasó texto donde iba un booleano.
  const conAmbos = cuerpoDeCierre(parteCerrable(), {
    usuarioOid: OID,
    commit: true,
    confirmado: true,
  });
  const conTexto = cuerpoDeCierre(parteCerrable(), {
    usuarioOid: OID,
    commit: "false",
    confirmado: "false",
  });

  assert.equal(conAmbos.commit, true);
  assert.equal(conAmbos.confirmado, true);
  assert.equal(conTexto.commit, undefined);
  assert.equal(conTexto.confirmado, undefined);
});

test("f009 R51: el cuerpo NO lleva ningún campo manuscrito del cliente", () => {
  // El DNI y las observaciones están en el parte y no viajan: este endpoint no
  // sube nada y no los necesita para nada.
  const cuerpo = cuerpoDeCierre(parteCerrable(), {
    usuarioOid: OID,
    correo: CORREO,
  });

  const serializado = JSON.stringify(cuerpo);
  assert.equal(serializado.includes("00000000T"), false);
  assert.equal(serializado.includes("manuscrito"), false);
});

test("f009: el cuerpo lleva exactamente las claves que el backend exige", () => {
  const cuerpo = cuerpoDeCierre(parteCerrable(), { usuarioOid: OID, correo: CORREO });

  assert.deepEqual(Object.keys(cuerpo).sort(), [
    "correo",
    "destino",
    "estado_archivo",
    "hash",
    "numero_incidencia",
    "usuario_oid",
    "veredicto",
  ]);
});

test("f009 R30: el correo solo viaja si lo hay, porque solo hace falta la primera vez", () => {
  // Quien ya tiene su correspondencia confirmada no necesita que se derive
  // ningún candidato, así que no hay motivo para pasear su correo.
  const cuerpo = cuerpoDeCierre(parteCerrable(), { usuarioOid: OID });

  assert.equal("correo" in cuerpo, false);
});

test("f009 R28: sin saber quién lo pide, no se compone ningún cierre", () => {
  // Sin identidad no se puede firmar la incidencia en el ERP, y firmarla con
  // un valor por defecto es exactamente lo que prohíbe la decisión D2.
  assert.throws(
    () => cuerpoDeCierre(parteCerrable(), {}),
    /identificador del usuario/,
  );
});

test("f009: componer el cuerpo de un parte no cerrable se niega, no lo apaña", () => {
  // No basta con no pintar el botón: aunque se pulse dos veces, aquí se para.
  assert.throws(
    () => cuerpoDeCierre(parteCerrable({ archivado: false }), { usuarioOid: OID }),
    /no se puede cerrar/,
  );
});

test("f009: el estado del archivo que se declara es el que el backend admite", () => {
  const cuerpo = cuerpoDeCierre(parteCerrable(), { usuarioOid: OID });

  assert.equal(cuerpo.estado_archivo, "archivado");
});
