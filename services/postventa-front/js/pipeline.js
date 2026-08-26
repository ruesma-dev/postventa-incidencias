// services/postventa-front/js/pipeline.js
// R8, R13-R22, R29 · La orquestación de UN parte, sin DOM.
//
// Recibe el cliente `api` inyectado, así que se prueba entero sin red. Aquí
// vive todo lo que DECIDE algo: qué se pide y en qué orden, cómo se compone el
// cuerpo de validación, qué es archivable y qué viaja al archivar. `app.js`
// solo mueve estado de Alpine y llama a esto.
//
// Dos cosas que el front NO puede hacer, y que el backend ya defiende:
//   1. Montar el cuerpo de /api/validar a mano. Solo se admite el cuerpo tal y
//      como lo emiten /api/extraer y /api/firma. Aquí se guardan las dos
//      respuestas ÍNTEGRAS y solo se cambia `campos[x].valor` (y su confianza,
//      D3) cuando una persona edita.
//   2. Mandar de más a /api/archivar. El endpoint acepta cinco campos y
//      ninguno es personal: el DNI y las observaciones no viajan (R29).

(function () {
  "use strict";

  /**
   * Los NUEVE campos del parte, en el orden del dominio
   * (`domain/models/extraccion.py::CAMPOS_DEL_PARTE`). El backend exige las
   * nueve claves y responde 400 si falta una (R18).
   */
  const CAMPOS_DEL_PARTE = [
    "promocion",
    "codigo_obra",
    "unidad",
    "numero_incidencia",
    "fecha_servicio",
    "descripcion",
    "dni_cliente",
    "observaciones",
    "numero_pagina",
  ];

  /** El umbral del dominio (`domain/models/firma.py::UMBRAL_CONFIANZA`). */
  const UMBRAL_CONFIANZA = 50;

  /** Lo que `/api/archivar` acepta, además del fichero. NADA personal (R29). */
  const CAMPOS_DE_ARCHIVO = [
    "hash",
    "codigo_obra",
    "numero_incidencia",
    "veredicto",
    "destino",
  ];

  const VEREDICTO_APTO = "apto";
  const DESTINO_ARCHIVO = "archivo_y_cierre";
  const DESTINO_COLA = "cola_validacion_humana";
  const DESTINO_REVISION = "revision_manual";

  /** Un valor vacío es `null`: el backend distingue «vacío» de «no leído». */
  function normalizarValor(valor) {
    if (valor === undefined || valor === null) {
      return null;
    }
    const texto = String(valor).trim();
    return texto === "" ? null : texto;
  }

  /**
   * Devuelve la extracción con las correcciones de la persona aplicadas (D3).
   *
   * Un campo que ha mirado y escrito una persona es el dato más fiable que
   * hay: viaja con `confianza_pct` 100 y queda marcado como `editado`, para
   * poder distinguir después lo que escribió alguien de lo que dijo la IA.
   *
   * No muta la entrada: la respuesta original de `/api/extraer` se conserva
   * íntegra para poder volver a ella.
   */
  function aplicarEdiciones(extraccion, ediciones) {
    const correcciones = ediciones || {};
    const campos = {};

    CAMPOS_DEL_PARTE.forEach(function (nombre) {
      const original = (extraccion && extraccion.campos && extraccion.campos[nombre]) || {};
      if (Object.prototype.hasOwnProperty.call(correcciones, nombre)) {
        campos[nombre] = {
          valor: normalizarValor(correcciones[nombre]),
          confianza_pct: 100,
          editado: true,
        };
      } else {
        campos[nombre] = {
          valor: original.valor === undefined ? null : original.valor,
          confianza_pct:
            original.confianza_pct === undefined ? 0 : original.confianza_pct,
        };
      }
    });

    return Object.assign({}, extraccion, { campos: campos });
  }

  /**
   * El cuerpo de `POST /api/validar` (R8, R16, R18).
   *
   * Las dos respuestas van **verbatim**, salvo los valores que haya corregido
   * una persona. La `traza` no se toca.
   */
  function cuerpoDeValidacion(extraccion, firma, ediciones) {
    return {
      extraccion: aplicarEdiciones(extraccion, ediciones),
      firma: firma,
    };
  }

  /** Los campos por debajo del umbral, que hay que mirar antes de nada (R15). */
  function camposDudosos(extraccion, umbral) {
    const limite = umbral === undefined ? UMBRAL_CONFIANZA : umbral;
    const campos = (extraccion && extraccion.campos) || {};
    return CAMPOS_DEL_PARTE.filter(function (nombre) {
      const campo = campos[nombre];
      return campo && Number(campo.confianza_pct) < limite;
    });
  }

  /** Verde / ámbar / rojo, a partir de `veredicto` y `destino` (R13). */
  function semaforoDe(validacion) {
    if (!validacion || !validacion.destino) {
      return "";
    }
    if (
      validacion.veredicto === VEREDICTO_APTO &&
      validacion.destino === DESTINO_ARCHIVO
    ) {
      return "verde";
    }
    if (validacion.destino === DESTINO_COLA) {
      return "ambar";
    }
    if (validacion.destino === DESTINO_REVISION) {
      return "rojo";
    }
    return "";
  }

  /** ¿Este parte se puede archivar? Apto Y con destino de archivo (R21). */
  function esArchivable(validacion) {
    return Boolean(
      validacion &&
        validacion.veredicto === VEREDICTO_APTO &&
        validacion.destino === DESTINO_ARCHIVO,
    );
  }

  /** El valor efectivo de un campo: la corrección de la persona si la hay. */
  function valorDeCampo(parte, nombre) {
    const ediciones = parte.ediciones || {};
    if (Object.prototype.hasOwnProperty.call(ediciones, nombre)) {
      return normalizarValor(ediciones[nombre]);
    }
    const campos = (parte.extraccion && parte.extraccion.campos) || {};
    return normalizarValor(campos[nombre] && campos[nombre].valor);
  }

  /**
   * El `multipart` de `POST /api/archivar`: el fichero y **cinco** campos (R20).
   *
   * Se niega a componer nada que no sea apto (R21) o que ya esté archivado.
   * No basta con no pintar el botón: aunque se pulse dos veces, aquí se para.
   */
  function cuerpoDeArchivo(parte, FabricaFormData) {
    if (!esArchivable(parte && parte.validacion)) {
      throw new Error(
        "este parte no es apto para archivo (hace falta veredicto 'apto' y " +
          "destino 'archivo_y_cierre')",
      );
    }
    if (parte.archivado) {
      throw new Error("este parte ya está archivado");
    }
    // F-019 R27 · el backend responde 409 a un parte que no consta guardado y
    // no sube nada. Pararlo aquí evita la petición inútil y, sobre todo, evita
    // que la pantalla ofrezca archivar algo que va a fallar: sin esto se
    // vuelve al defecto 15 con el usuario delante.
    if (!parte.guardado) {
      throw new Error(
        "este parte no se ha guardado todavía, así que no se puede archivar: " +
          (parte.errorGuardado ||
            "hay que guardarlo antes (POST /api/parte)"),
      );
    }

    const Fabrica =
      FabricaFormData || (typeof FormData !== "undefined" ? FormData : null);
    if (!Fabrica) {
      throw new Error("este entorno no tiene FormData");
    }

    const cuerpo = new Fabrica();
    cuerpo.append("fichero", parte.fichero, parte.fichero && parte.fichero.name);
    cuerpo.append("hash", parte.hash);
    cuerpo.append("codigo_obra", valorDeCampo(parte, "codigo_obra") || "");
    cuerpo.append("numero_incidencia", valorDeCampo(parte, "numero_incidencia") || "");
    cuerpo.append("veredicto", parte.validacion.veredicto);
    cuerpo.append("destino", parte.validacion.destino);
    return cuerpo;
  }

  /**
   * Reconstruye el PDF de un parte desde el base64 de `/api/split` (R14).
   *
   * Se devuelve un `File` en memoria: el PDF nunca viaja en una URL con el
   * contenido dentro, y quien lo pinte tiene que revocar su objeto URL al
   * cerrar el parte (22 blobs vivos es memoria que no vuelve).
   */
  function ficheroDeParte(parte, herramientas) {
    const utiles = herramientas || {};
    const decodificar =
      utiles.atob || (typeof atob !== "undefined" ? atob : null);
    const FabricaFile = utiles.File || (typeof File !== "undefined" ? File : null);

    if (!parte || !parte.contenido_b64) {
      throw new Error(
        `el parte ${parte && parte.hash} no trae contenido_b64: no se puede ` +
          "mostrar su PDF",
      );
    }
    if (!decodificar || !FabricaFile) {
      throw new Error("este entorno no sabe decodificar base64 a fichero");
    }

    const binario = decodificar(parte.contenido_b64);
    const bytes = new Uint8Array(binario.length);
    for (let i = 0; i < binario.length; i += 1) {
      bytes[i] = binario.charCodeAt(i);
    }
    return new FabricaFile([bytes], `parte-${String(parte.hash).slice(0, 8)}.pdf`, {
      type: "application/pdf",
    });
  }

  /**
   * Procesa UN parte: extraer y firma **en paralelo**, y validar después (R8).
   *
   * Van en paralelo a propósito: componerlas sumaría dos timeouts de 120 s
   * bajo el corte de 230 s de la Function.
   *
   * @returns {Promise<{extraccion, firma, validacion}>} Las tres respuestas
   *          íntegras, que es lo que hace posible revalidar sin gastar IA.
   */
  async function procesarParte(parte, api, remesaId) {
    const resultados = await Promise.all([
      api.extraer(parte.fichero, parte.hash),
      api.firma(parte.fichero, parte.hash),
    ]);
    const extraccion = resultados[0];
    const firma = resultados[1];

    const validacion = await api.validar(
      cuerpoDeValidacion(extraccion, firma, parte.ediciones),
      parte.hash,
    );

    // F-019 R26 · guardar va DESPUÉS de validar y ANTES de ofrecer archivar.
    // No se lanza si falla: el veredicto ya está pagado —dos llamadas de IA— y
    // tirarlo obligaría a repetirlas. Lo que se devuelve es por qué no se pudo
    // guardar, y con eso el parte queda marcado como no archivable (R27).
    const guardado = await guardarParte(
      Object.assign({}, parte, { extraccion: extraccion, firma: firma }),
      api,
      remesaId,
    );

    return {
      extraccion: extraccion,
      firma: firma,
      validacion: validacion,
      guardado: guardado,
    };
  }

  /**
   * El cuerpo de `POST /api/parte` (F-019 R26).
   *
   * Es **el de `/api/validar` más dos claves**, y es deliberado: así no hay
   * dos formas de describir el mismo parte, que es como divergen los
   * contratos. El backend usa los mismos parsers para los dos.
   *
   * Ojo con el nombre: `js/api.js` tiene otro `cuerpoDeParte`, que compone el
   * `multipart` de `/api/extraer` y `/api/firma`. Este compone JSON y **no
   * lleva los bytes del PDF** (R12): el documento vive en SharePoint.
   *
   * La extracción va con las correcciones de la persona aplicadas, para que lo
   * guardado sea **lo revisado** y no lo que dijo la IA la primera vez (R28).
   */
  function cuerpoDeParte(parte, remesaId) {
    return {
      remesa_id: remesaId,
      parte: {
        hash: parte.hash,
        origen: parte.origen,
        paginas_origen: parte.paginas_origen,
        modo_deteccion: parte.modo_deteccion,
      },
      extraccion: aplicarEdiciones(parte.extraccion, parte.ediciones),
      firma: parte.firma,
    };
  }

  /**
   * Guarda el parte y su veredicto. **Nunca lanza** (F-019 R27).
   *
   * Devuelve `{ok, motivo}`. Un guardado fallido no es un error del proceso:
   * es un parte que **no se puede archivar**, y quien lo mire tiene que ver
   * por qué. Dejarlo escapar como excepción marcaría el parte como «error de
   * lectura», que es otra cosa y se arregla de otra manera.
   *
   * Sin `remesaId` ni se intenta: el backend respondería 409 y la petición
   * sería ruido. El motivo lo dice, porque quien lo lea tiene que saber que
   * hay que volver a subir la remesa.
   */
  async function guardarParte(parte, api, remesaId) {
    if (!remesaId) {
      return {
        ok: false,
        motivo:
          "no hay ninguna remesa registrada para este parte: vuelve a subir " +
          "la remesa para que quede constancia antes de guardar sus partes",
      };
    }
    try {
      await api.guardarParte(cuerpoDeParte(parte, remesaId), parte.hash);
      return { ok: true, motivo: "" };
    } catch (error) {
      return {
        ok: false,
        motivo:
          (error && error.mensaje) ||
          (error && error.message) ||
          String(error),
      };
    }
  }

  /**
   * Revalida el parte corregido y **vuelve a guardarlo** (F-019 R28).
   *
   * Las dos cosas van juntas a propósito: si se revalidara sin guardar, lo
   * que quedaría en la base sería el veredicto anterior —el que emitió la IA
   * sobre el dato sin corregir— y la persona que revisó el parte no tendría
   * forma de saberlo.
   *
   * `revalidar` se mantiene aparte y sin tocar: es el contrato de F-007 R17
   * —una sola petición, sin IA— y hay quien solo quiere el veredicto.
   */
  async function revalidarYGuardar(parte, api, remesaId) {
    const validacion = await revalidar(parte, api);
    const guardado = await guardarParte(parte, api, remesaId);
    return { validacion: validacion, guardado: guardado };
  }

  /**
   * Revalida un parte ya corregido: **solo** `POST /api/validar` (R17).
   *
   * `/api/validar` no gasta IA, y esa es justo la razón de que exista
   * separado. Volver a llamar a extraer o a firma sería tirar dos llamadas
   * multimodales por cada corrección de una letra.
   */
  function revalidar(parte, api) {
    if (!parte || !parte.extraccion || !parte.firma) {
      return Promise.reject(
        new Error(
          "este parte todavía no tiene extracción y firma: no se puede " +
            "revalidar sin haberlo procesado antes",
        ),
      );
    }
    return api.validar(
      cuerpoDeValidacion(parte.extraccion, parte.firma, parte.ediciones),
      parte.hash,
    );
  }

  const Pipeline = {
    CAMPOS_DEL_PARTE: CAMPOS_DEL_PARTE,
    CAMPOS_DE_ARCHIVO: CAMPOS_DE_ARCHIVO,
    UMBRAL_CONFIANZA: UMBRAL_CONFIANZA,
    normalizarValor: normalizarValor,
    aplicarEdiciones: aplicarEdiciones,
    cuerpoDeValidacion: cuerpoDeValidacion,
    camposDudosos: camposDudosos,
    semaforoDe: semaforoDe,
    esArchivable: esArchivable,
    valorDeCampo: valorDeCampo,
    cuerpoDeArchivo: cuerpoDeArchivo,
    cuerpoDeParte: cuerpoDeParte,
    ficheroDeParte: ficheroDeParte,
    procesarParte: procesarParte,
    guardarParte: guardarParte,
    revalidar: revalidar,
    revalidarYGuardar: revalidarYGuardar,
  };

  if (typeof window !== "undefined") {
    window.Pipeline = Pipeline;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = Pipeline;
  }
})();
