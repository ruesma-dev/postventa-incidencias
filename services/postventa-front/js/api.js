// services/postventa-front/js/api.js
// R12, R23-R27 · El cliente de los diez endpoints del backend.
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
// F-002 … F-006. F-019 añade tres —`registrarRemesa`, `guardarParte` y
// `cola`— y F-009 añade `cerrar`, el único que escribe en el ERP de
// producción. Ninguno de los dos cambia los que ya estaban.

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

  /**
   * F-009 · Quién es el usuario, según lo que devuelve el proxy de la SWA.
   *
   * Función **pura**, y por eso comprobable: entra el JSON de `/.auth/me` y
   * sale `{usuarioOid, correo}`. La petición es aparte.
   *
   * Dos cosas que no son obvias y que deciden qué se guarda:
   *
   * - **El `oid` de Entra está en los `claims`, no en `userId`.** `userId` es
   *   el identificador que la Static Web App inventa para la sesión, y no es
   *   el mismo que el `oid` del directorio. Se prefiere el `oid` porque es lo
   *   que el backend guarda en la traza del cierre y en la correspondencia
   *   con el ERP: si mañana cambiara, la persona perdería su login mapeado.
   * - **Esto NO es una identidad verificada.** La cabecera del proxy va sin
   *   firmar. Sirve para saber quién dice ser el usuario; quién puede cerrar
   *   lo decide el grupo de Posventa en la plataforma, y con qué login se
   *   firma lo decide el ERP.
   */
  function identidadDe(datos) {
    const principal = (datos && datos.clientPrincipal) || null;
    if (!principal) {
      return { usuarioOid: "", correo: "" };
    }

    const claims = principal.claims || [];
    const valorDe = function (sufijos) {
      const encontrado = claims.find(function (claim) {
        const tipo = String((claim && claim.typ) || "");
        return sufijos.some(function (sufijo) {
          return tipo === sufijo || tipo.endsWith("/" + sufijo);
        });
      });
      return (encontrado && encontrado.val) || "";
    };

    return {
      usuarioOid: valorDe(["objectidentifier", "oid"]) || principal.userId || "",
      correo:
        valorDe(["preferred_username", "emailaddress", "email", "upn"]) ||
        principal.userDetails ||
        "",
    };
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
    // F-009 · lo sirve el proxy de la Static Web App, NO este backend, y
    // por eso va aparte del prefijo de la API. Inyectable para que la
    // suite no dependa de una ruta que en local no existe.
    const rutaIdentidad = ajustes.rutaIdentidad || "/.auth/me";
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

      /**
       * F-019 R25 · deja constancia de la remesa y devuelve su `remesa_id`.
       *
       * Va **antes** de procesar ningún parte: `postventa.partes.remesa_id`
       * tiene clave ajena contra `postventa.remesas.id`, así que sin esto el
       * guardado de cada parte responde 409.
       *
       * El `remesa_id` que devuelve se conserva mientras dure la remesa en
       * pantalla y se reenvía en cada guardado: `postventa.remesas` no tiene
       * clave natural (decisión D2), así que resubir sin él crearía una fila
       * de remesa de más.
       */
      registrarRemesa: function (cuerpo) {
        return peticion("/remesa", {
          metodo: "POST",
          cuerpo: JSON.stringify(cuerpo),
          cabeceras: { "Content-Type": "application/json" },
          paso: "remesa",
        });
      },

      /**
       * F-019 R26 · guarda el parte y su veredicto.
       *
       * El cuerpo lo compone `js/pipeline.js::cuerpoDeParte` (es el de
       * `/api/validar` más `remesa_id` y el bloque `parte`). **No lleva los
       * bytes del PDF**: el documento vive en SharePoint y el disco del
       * servidor es compartido.
       *
       * El veredicto que viaja dentro es informativo: el backend lo
       * **recalcula** con las reglas del dominio y no acepta el del cuerpo.
       */
      guardarParte: function (cuerpo, hash) {
        return peticion("/parte", {
          metodo: "POST",
          cuerpo: JSON.stringify(cuerpo),
          cabeceras: { "Content-Type": "application/json" },
          paso: "parte",
          hash: hash,
        });
      },

      /**
       * F-026 · registra que una persona aprueba este parte.
       *
       * **Endpoint propio** y no una clave más en `/api/parte` (R18): guardar
       * ocurre en cada revalidación, y aprobar es una decisión de una persona.
       * Una petición, una decisión, una fila de auditoría.
       *
       * El cuerpo lo compone `js/pipeline.js::cuerpoDeAprobacion`: el de
       * `/api/parte` más `usuario_oid` y `confirmado`. **No lleva los bytes
       * del PDF** ni ningún veredicto ya hecho — el backend lo recalcula con
       * las reglas del dominio y no acepta el del cuerpo (R5).
       *
       * Devuelve el bloque `aprobacion` que hay que pintar (R22). Un **409**
       * es «este parte no es aprobable», y no se reintenta: insistir no lo
       * vuelve aprobable.
       */
      aprobar: function (cuerpo, hash) {
        return peticion("/aprobar", {
          metodo: "POST",
          cuerpo: JSON.stringify(cuerpo),
          cabeceras: { "Content-Type": "application/json" },
          paso: "aprobar",
          hash: hash,
        });
      },

      /**
       * F-019 · la cola de validación humana, que sobrevive entre sesiones.
       *
       * El `limite` es opcional; el backend aplica 50 por omisión y **acota
       * duro a 500** venga lo que venga, así que aquí no hace falta repetir
       * el techo: repetirlo daría dos números que divergirían.
       */
      cola: function (limite) {
        const ruta =
          limite === undefined || limite === null
            ? "/cola"
            : "/cola?limite=" + encodeURIComponent(limite);
        return peticion(ruta, { metodo: "GET", paso: "cola" });
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

      /**
       * F-012 · adjunta el parte a la reclamación como gráfico de Sigrid.
       *
       * **Va delante de `cerrar`**, y ese orden es la mitad de la feature:
       * ninguna reclamación se cierra sin su parte dentro del ERP.
       *
       * Va como `FormData` y no como JSON —al revés que `cerrar`— porque lo
       * que se adjunta **son los bytes del PDF**, los mismos que se mandaron a
       * `archivar`. El cuerpo lo compone `js/pipeline.js::cuerpoDeGrafico`.
       *
       * **Por omisión no escribe nada**: sin `commit` el backend responde el
       * dry-run —nombre, clase, tamaño, `sha256` y los avisos de la pasarela—.
       *
       * **Ese dry-run ya no se le enseña a nadie** (R40 de F-025, que deroga
       * R63 de F-012): hay **una** confirmación para las tres escrituras y el
       * front llama siempre con `commit`. La comprobación previa no ha
       * desaparecido —se ejecuta dentro de la misma llamada que escribe, ver
       * `design.md` §2 de F-025—; lo que desapareció es la pantalla. Quien
       * lea esto dentro de seis meses: reponerla no es arreglar nada.
       *
       * Un 503 aquí es la **puerta de entorno**, igual que en `archivar` y en
       * `cerrar`: no es un fallo y no se reintenta. Insistir no la ablanda.
       *
       * Lo transitorio —502, red, tiempo agotado— sí se reintenta, como en
       * todos los pasos, y aquí es **seguro por construcción**: el endpoint de
       * la pasarela es idempotente por tamaño y `sha256`, así que un reintento
       * no cuelga un segundo gráfico.
       */
      adjuntar: function (formData, hash) {
        return peticion("/adjuntar", {
          metodo: "POST",
          cuerpo: formData,
          paso: "adjuntar",
          hash: hash,
        });
      },

      /**
       * F-009 · cierra la incidencia en Sigrid, o enseña qué pasaría.
       *
       * **Por omisión no cierra nada.** El cuerpo lo compone
       * `js/pipeline.js::cuerpoDeCierre`, y sin `commit` el backend responde
       * el dry-run: los dos estados legibles, con qué login se firmaría y el
       * bloque `grafico` con el estado real de este parte —`adjuntado`,
       * `dry_run_ok` o `no_consta`— (R49).
       *
       * **Ese dry-run ya no se le enseña a nadie** (R40 de F-025, que deroga
       * R63 de F-012): hay **una** confirmación para las tres escrituras y el
       * front llama siempre con `commit`. La comprobación previa no ha
       * desaparecido —se ejecuta dentro de la misma llamada que escribe, ver
       * `design.md` §2 de F-025—; lo que desapareció es la pantalla. Quien
       * lea esto dentro de seis meses: reponerla no es arreglar nada, es
       * deshacer una decisión fechada del responsable.
       *
       * Lo que ese bloque **sustituye** es el `aviso_sin_grafico` de F-009,
       * derogado por R48 de F-012: ya no llega en la respuesta y no hay que
       * buscarlo. Desde F-012 el cierre con `commit` **exige** el gráfico
       * adjuntado (R2), así que aquel aviso —«quedará cerrada sin el parte»—
       * sería falso; en su sitio va el estado real, leído de la traza propia.
       *
       * **No lleva los bytes del PDF**, y por eso va como JSON y no como
       * `FormData`: este endpoint no sube nada, solo mueve un estado.
       *
       * Un 503 aquí es la **puerta de entorno del cierre**, igual que en
       * `archivar`: no es un fallo y no se reintenta. Insistir no la ablanda.
       */
      cerrar: function (cuerpo, hash) {
        return peticion("/cerrar", {
          metodo: "POST",
          cuerpo: JSON.stringify(cuerpo),
          cabeceras: { "Content-Type": "application/json" },
          paso: "cerrar",
          hash: hash,
        });
      },

      /**
       * F-009 · quién es el usuario de la sesión, para poder firmar el cierre.
       *
       * **No va contra `/api`**: `/.auth/me` lo sirve el proxy de la Static Web
       * App, no este backend. Por eso no pasa por `peticion()` —que antepone el
       * prefijo y aplica los reintentos del contrato del backend— y usa el
       * `fetch` inyectado directamente.
       *
       * **Nunca falla hacia arriba.** Si el proxy no responde, o responde algo
       * que no es JSON, se devuelve la identidad vacía: sin ella el botón de
       * cerrar se queda deshabilitado, que es lo correcto —no se firma un
       * cierre a nombre de nadie—, pero la pantalla sigue sirviendo para
       * validar y archivar. Reventar aquí dejaría inservible todo lo demás por
       * un endpoint que en local ni siquiera existe.
       */
      identidad: async function () {
        try {
          const respuesta = await hacerFetch(rutaIdentidad, { method: "GET" });
          const texto = await respuesta.text();
          return identidadDe(JSON.parse(texto));
        } catch (error) {
          return { usuarioOid: "", correo: "" };
        }
      },
    };
  }

  const Api = {
    crearApi: crearApi,
    ErrorApi: ErrorApi,
    clasificar: clasificar,
    identidadDe: identidadDe,
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
