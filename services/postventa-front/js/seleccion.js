// services/postventa-front/js/seleccion.js
// R1-R4 · Qué entra en la remesa y cómo se envía.
//
// Lógica pura: recibe un array de `File` (o cualquier cosa con `name` y
// `size`) y no toca el DOM. Eso es lo que la hace probable con `node --test`
// sin navegador.
//
// El detalle que parece cosmético y no lo es: cada fichero viaja con un NOMBRE
// DE CAMPO DISTINTO (`fichero_0`, `fichero_1`, ...). El backend lee
// `req.files.values()`, que devuelve **un valor por clave**; con el mismo
// nombre de campo repetido, una remesa de 3 PDFs entraría como 1 y los otros
// dos se perderían en silencio.

(function () {
  "use strict";

  /** Lo único que el backend sabe trocear. */
  const EXTENSIONES_ADMITIDAS = [".pdf", ".zip"];

  /** Texto para el usuario cuando la selección no sirve (R3). */
  const TEXTO_FORMATOS =
    "Solo se admiten ficheros PDF (.pdf) y ZIP (.zip) con partes escaneados.";

  /** Prefijo del nombre de campo del multipart (R4). */
  const PREFIJO_CAMPO = "fichero_";

  function extensionDe(nombre) {
    const texto = String(nombre || "");
    const punto = texto.lastIndexOf(".");
    return punto === -1 ? "" : texto.slice(punto).toLowerCase();
  }

  /** ¿Este fichero entra en la remesa? */
  function esAdmitido(fichero) {
    return EXTENSIONES_ADMITIDAS.indexOf(extensionDe(fichero && fichero.name)) !== -1;
  }

  /**
   * Tamaño legible para la lista de la zona de carga (R1).
   *
   * Se queda en MB: un parte escaneado son unos pocos MB y una remesa entera
   * no llega a GB.
   */
  function formatearTamano(bytes) {
    const numero = Number(bytes);
    if (!Number.isFinite(numero) || numero < 0) {
      return "tamaño desconocido";
    }
    if (numero < 1024) {
      return `${numero} B`;
    }
    if (numero < 1024 * 1024) {
      return `${(numero / 1024).toFixed(1)} KB`;
    }
    return `${(numero / (1024 * 1024)).toFixed(1)} MB`;
  }

  /**
   * Separa la selección en lo que entra y lo que se descarta (R1, R2).
   *
   * @param {Array} ficheros Lo que ha soltado el usuario o ha traído el
   *        selector de carpeta. Una carpeta trae de todo: fotos, hojas de
   *        cálculo, `Thumbs.db`.
   * @returns {{admitidos: Array, descartados: Array<{nombre: string, motivo: string}>,
   *            mensajeDescartes: string}}
   *          `mensajeDescartes` dice CUÁNTOS se han descartado y por qué; es
   *          cadena vacía si no se descartó ninguno.
   */
  function filtrarAdmitidos(ficheros) {
    const entrada = Array.isArray(ficheros) ? ficheros : Array.from(ficheros || []);
    const admitidos = [];
    const descartados = [];

    entrada.forEach(function (fichero) {
      if (esAdmitido(fichero)) {
        admitidos.push(fichero);
      } else {
        const extension = extensionDe(fichero && fichero.name);
        descartados.push({
          nombre: (fichero && fichero.name) || "(sin nombre)",
          motivo: extension
            ? `formato ${extension} no admitido`
            : "sin extensión reconocible",
        });
      }
    });

    return {
      admitidos: admitidos,
      descartados: descartados,
      mensajeDescartes: descartados.length
        ? `Se han descartado ${descartados.length} fichero(s) que no son .pdf ni .zip.`
        : "",
    };
  }

  /**
   * ¿Hay que rechazar la selección entera sin llamar a nadie? (R3)
   *
   * @returns {string} El motivo para el usuario, o cadena vacía si la
   *          selección es utilizable. Devolver texto y no un booleano evita
   *          que quien llama tenga que inventarse el mensaje.
   */
  function motivoDeRechazo(resultado) {
    if (!resultado || !resultado.admitidos || resultado.admitidos.length === 0) {
      return `La selección no contiene ningún PDF ni ZIP. ${TEXTO_FORMATOS}`;
    }
    return "";
  }

  /**
   * Construye el `multipart/form-data` de `POST /api/split` (R4).
   *
   * @param {Array} ficheros Los ya admitidos.
   * @param {Function} [FabricaFormData] Inyectable para los tests; por defecto
   *        el `FormData` del entorno.
   * @returns {FormData} Un campo por fichero: `fichero_0`, `fichero_1`, ...
   */
  function formDataDeRemesa(ficheros, FabricaFormData) {
    const entrada = Array.isArray(ficheros) ? ficheros : Array.from(ficheros || []);
    if (entrada.length === 0) {
      throw new Error("no hay ningún fichero admitido que enviar");
    }

    const Fabrica =
      FabricaFormData || (typeof FormData !== "undefined" ? FormData : null);
    if (!Fabrica) {
      throw new Error("este entorno no tiene FormData");
    }

    const cuerpo = new Fabrica();
    entrada.forEach(function (fichero, indice) {
      // El índice, y NO el nombre del fichero: dos ficheros pueden llamarse
      // igual (dos carpetas distintas) y el backend perdería uno.
      cuerpo.append(PREFIJO_CAMPO + indice, fichero, fichero.name);
    });
    return cuerpo;
  }

  const Seleccion = {
    EXTENSIONES_ADMITIDAS: EXTENSIONES_ADMITIDAS,
    TEXTO_FORMATOS: TEXTO_FORMATOS,
    PREFIJO_CAMPO: PREFIJO_CAMPO,
    extensionDe: extensionDe,
    esAdmitido: esAdmitido,
    formatearTamano: formatearTamano,
    filtrarAdmitidos: filtrarAdmitidos,
    motivoDeRechazo: motivoDeRechazo,
    formDataDeRemesa: formDataDeRemesa,
  };

  if (typeof window !== "undefined") {
    window.Seleccion = Seleccion;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = Seleccion;
  }
})();
