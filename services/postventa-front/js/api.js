// services/postventa-front/js/api.js
// R12, R23-R27 · El cliente de los seis endpoints del backend.
//
// Una sola forma de hablar con el backend y una sola forma de error hacia
// arriba: `ErrorApi {tipo, http, mensaje, avisos}` con
// `tipo ∈ {transitorio, peticion, no_apto, entorno, desconocido}`.
//
// Lo que se inyecta (y por qué): `fetch`, `esperar` y `programarTimeout`. Así
// los reintentos de R23 se prueban en milisegundos, sin relojes falsos y sin
// abrir una sola conexión en la suite.
//
// NINGUNO de estos endpoints se toca en F-007: el contrato es el que dejaron
// F-002 … F-006.

(function () {
  "use strict";

  const TrazaModulo =
    (typeof window !== "undefined" && window.Traza) ||
    (typeof require !== "undefined" ? require("./traza.js") : null);

  /** El error que sale de este módulo. Siempre este, nunca uno crudo. */
  class ErrorApi extends Error {
    constructor(tipo, http, mensaje, avisos) {
      super(mensaje);
      this.name = "ErrorApi";
      this.tipo = tipo;
      this.http = http === undefined ? null : http;
      this.mensaje = mensaje;
      this.avisos = avisos || [];
    }
  }

  /** Configuración por defecto; `js/config.js` manda sobre esto. */
  const CONFIG_POR_DEFECTO = {
    TIMEOUT_PETICION_MS: 180000,
    REINTENTOS: 2,
    ESPERAS_MS: [1000, 3000],
  };

  const TEXTO_ENTORNO_NO_ARCHIVA =
    "Este entorno no archiva: la puerta de entorno del backend está apagada. " +
    "No es un fallo y no hay nada que arreglar aquí.";

  /**
   * Clasifica una respuesta ya leída. Función pura, y por eso comprobable.
   *
   * @returns {ErrorApi|null} `null` si la respuesta es buena.
   */
  function clasificar(status, datos) {
    if (datos === undefined) {
      // No era JSON: puede ser la página de error del proxy o de la SWA (R26).
      return new ErrorApi(
        "desconocido",
        status,
        `Respuesta inesperada del servicio (HTTP ${status}).`,
      );
    }

    if (status >= 200 && status < 300) {
      return null;
    }

    const mensaje =
      (datos && typeof datos.error === "string" && datos.error) ||
      `El servicio respondió ${status}.`;
    const avisos = (datos && datos.avisos) || [];

    if (status === 502) {
      return new ErrorApi("transitorio", status, mensaje, avisos);
    }
    if (status === 503) {
      return new ErrorApi("entorno", status, TEXTO_ENTORNO_NO_ARCHIVA, avisos);
    }
    if (status === 409) {
      return new ErrorApi("no_apto", status, mensaje, avisos);
    }
    if (status === 400 || status === 413) {
      return new ErrorApi("peticion", status, mensaje, avisos);
    }
    // Cualquier otro código: no se reintenta, porque no hay razón para creer
    // que mejore, y se enseña tal cual en vez de esconderlo.
    return new ErrorApi("desconocido", status, mensaje, avisos);
  }

  /** Traduce el fallo de `fetch` (red caída, aborto por timeout) a `ErrorApi`. */
  function errorDeTransporte(error) {
    if (error && error.name === "AbortError") {
      return new ErrorApi(
        "transitorio",
        null,
        "La petición tardó demasiado y se canceló. Reintentando…",
      );
    }
    return new ErrorApi(
      "transitorio",
      null,
      "No se pudo contactar con el servicio. Reintentando…",
    );
  }

  /**
   * Crea el cliente.
   *
   * @param {Object} opciones
   * @param {string} [opciones.baseApi] Prefijo de los endpoints (`/api`).
   * @param {Object} [opciones.config] `TIMEOUT_PETICION_MS`, `REINTENTOS`, `ESPERAS_MS`.
   * @param {Function} [opciones.fetch] Inyectable: los tests no abren red.
   * @param {Function} [opciones.esperar] `(ms) => Promise`. Inyectable: el
   *        backoff de R23 se prueba sin esperar 4 segundos de verdad.
   * @param {Function} [opciones.programarTimeout] `(ms, cb) => cancelar`.
   * @param {Function} [opciones.traza] El registro; por defecto, `js/traza.js`.
   */
  function crearApi(opciones) {
    const ajustes = opciones || {};
    const baseApi = ajustes.baseApi || "/api";
    const config = Object.assign({}, CONFIG_POR_DEFECTO, ajustes.config || {});
    const hacerFetch =
      ajustes.fetch || (typeof fetch !== "undefined" ? fetch.bind(null) : null);
    const esperar =
      ajustes.esperar ||
      function (ms) {
        return new Promise(function (res) {
          setTimeout(res, ms);
        });
      };
    const programarTimeout =
      ajustes.programarTimeout ||
      function (ms, alDispararse) {
        const id = setTimeout(alDispararse, ms);
        return function () {
          clearTimeout(id);
        };
      };
    const registrar =
      ajustes.traza || (TrazaModulo ? TrazaModulo.traza : function () {});

    /** Un intento: una petición, sin reintentos. */
    async function unIntento(ruta, opcionesPeticion) {
      const abortador = new AbortController();
      const cancelarTimeout = programarTimeout(
        config.TIMEOUT_PETICION_MS,
        function () {
          // Sin esto, una petición colgada dejaría su plaza de la cola
          // ocupada para siempre (R12).
          abortador.abort();
        },
      );

      let respuesta;
      try {
        respuesta = await hacerFetch(baseApi + ruta, {
          method: opcionesPeticion.metodo,
          body: opcionesPeticion.cuerpo,
          headers: opcionesPeticion.cabeceras,
          signal: abortador.signal,
        });
      } catch (error) {
        throw errorDeTransporte(error);
      } finally {
        cancelarTimeout();
      }

      const textoCrudo = await respuesta.text();
      let datos;
      try {
        datos = JSON.parse(textoCrudo);
      } catch (error) {
        datos = undefined; // no era JSON: lo clasifica `clasificar` (R26)
      }

      const problema = clasificar(respuesta.status, datos);
      if (problema) {
        problema.http = respuesta.status;
        throw problema;
      }
      return { datos: datos, http: respuesta.status };
    }

    /**
     * Una petición completa: timeout, reintentos con backoff y traza.
     *
     * Solo se reintenta lo `transitorio` (R23). Un 400 no mejora repitiéndolo,
     * y un 503 de archivar es la puerta de entorno: insistir no la ablanda.
     */
    async function peticion(ruta, opcionesPeticion) {
      const datosPeticion = opcionesPeticion || {};
      const paso = datosPeticion.paso || ruta.replace("/", "");
      const hash = datosPeticion.hash || "";
      const maximoReintentos = config.REINTENTOS;
      const esperas = config.ESPERAS_MS || [];

      for (let intento = 0; ; intento += 1) {
        try {
          const resultado = await unIntento(ruta, datosPeticion);
          registrar({ hash: hash, paso: paso, estado: "ok", http: resultado.http });
          return resultado.datos;
        } catch (error) {
          const fallo =
            error instanceof ErrorApi
              ? error
              : new ErrorApi("desconocido", null, String(error && error.message));

          const quedanIntentos = intento < maximoReintentos;
          registrar({
            hash: hash,
            paso: paso,
            estado:
              fallo.tipo === "transitorio" && quedanIntentos
                ? "reintentando"
                : fallo.tipo,
            http: fallo.http,
          });

          if (fallo.tipo === "transitorio" && quedanIntentos) {
            const espera = esperas[intento] !== undefined
              ? esperas[intento]
              : esperas[esperas.length - 1];
            await esperar(espera);
            continue;
          }
          throw fallo;
        }
      }
    }

    /** Multipart de `/api/extraer` y `/api/firma`: el fichero y su hash. */
    function cuerpoDeParte(fichero, hash, FabricaFormData) {
      const Fabrica =
        FabricaFormData || (typeof FormData !== "undefined" ? FormData : null);
      if (!Fabrica) {
        throw new Error("este entorno no tiene FormData");
      }
      const cuerpo = new Fabrica();
      cuerpo.append("fichero", fichero, fichero && fichero.name);
      cuerpo.append("hash", hash);
      return cuerpo;
    }

    return {
      peticion: peticion,
      cuerpoDeParte: cuerpoDeParte,

      /** R27 · estado del servicio. */
      salud: function () {
        return peticion("/health", { metodo: "GET", paso: "salud" });
      },

      /** R4 · una sola petición con la remesa entera. */
      trocear: function (formData) {
        // Sin `Content-Type` a mano: lo pone el navegador con su `boundary`.
        return peticion("/split", {
          metodo: "POST",
          cuerpo: formData,
          paso: "split",
        });
      },

      /** R8 · extracción de los nueve campos. */
      extraer: function (fichero, hash) {
        return peticion("/extraer", {
          metodo: "POST",
          cuerpo: cuerpoDeParte(fichero, hash),
          paso: "extraer",
          hash: hash,
        });
      },

      /** R8 · clasificación de la firma. */
      firma: function (fichero, hash) {
        return peticion("/firma", {
          metodo: "POST",
          cuerpo: cuerpoDeParte(fichero, hash),
          paso: "firma",
          hash: hash,
        });
      },

      /** R17 · revalidar es UNA petición y no gasta IA. */
      validar: function (cuerpo, hash) {
        return peticion("/validar", {
          metodo: "POST",
          cuerpo: JSON.stringify(cuerpo),
          cabeceras: { "Content-Type": "application/json" },
          paso: "validar",
          hash: hash,
        });
      },

      /** R20 · archivo. El `FormData` lo compone `js/pipeline.js` (R29). */
      archivar: function (formData, hash) {
        return peticion("/archivar", {
          metodo: "POST",
          cuerpo: formData,
          paso: "archivar",
          hash: hash,
        });
      },
    };
  }

  const Api = {
    crearApi: crearApi,
    ErrorApi: ErrorApi,
    clasificar: clasificar,
    CONFIG_POR_DEFECTO: CONFIG_POR_DEFECTO,
    TEXTO_ENTORNO_NO_ARCHIVA: TEXTO_ENTORNO_NO_ARCHIVA,
  };

  if (typeof window !== "undefined") {
    window.Api = Api;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = Api;
  }
})();
