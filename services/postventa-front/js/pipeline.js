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
  async function procesarParte(parte, api) {
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

    return { extraccion: extraccion, firma: firma, validacion: validacion };
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
    ficheroDeParte: ficheroDeParte,
    procesarParte: procesarParte,
    revalidar: revalidar,
  };

  if (typeof window !== "undefined") {
    window.Pipeline = Pipeline;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = Pipeline;
  }
})();
