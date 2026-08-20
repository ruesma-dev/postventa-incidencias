// services/postventa-front/js/traza.js
// R28 · El ÚNICO registro que el front puede emitir.
//
// Los partes traen DNI y observaciones manuscritas de clientes reales. Se ven
// en pantalla porque quien revisa los necesita, pero no se escriben en ningún
// registro: ni consola, ni localStorage, ni sessionStorage, ni URL.
//
// Esto es un FILTRO, no una convención: `traza()` se queda con cuatro claves
// (`hash`, `paso`, `estado`, `http`) y tira todo lo demás. Aunque alguien le
// pase el parte entero por descuido, lo personal no sale. Lo prueba
// `tests_js/traza.test.js`.
//
// Y por eso `console` no se llama desde ningún otro módulo del front: si el
// registro pasa por un solo sitio, basta con vigilar ese sitio.

(function () {
  "use strict";

  /** Las únicas claves que salen de aquí. Cualquier otra se descarta. */
  const CLAVES_PERMITIDAS = ["hash", "paso", "estado", "http"];

  /**
   * ¿Es un valor seguro de registrar tal cual?
   *
   * Solo primitivos. Un objeto o un array anidado podría traer dentro un campo
   * personal —`{valor: "12345678Z"}`— y el filtro por claves no lo vería.
   */
  function esPrimitivo(valor) {
    return (
      typeof valor === "string" ||
      typeof valor === "number" ||
      typeof valor === "boolean"
    );
  }

  /**
   * Devuelve SOLO las cuatro claves permitidas, y solo si son primitivas.
   *
   * @param {Object} evento Cualquier objeto. No se modifica.
   * @returns {{hash?: string, paso?: string, estado?: string, http?: number}}
   */
  function sanear(evento) {
    const limpio = {};
    if (evento === null || typeof evento !== "object") {
      return limpio;
    }
    CLAVES_PERMITIDAS.forEach(function (clave) {
      const valor = evento[clave];
      if (valor !== undefined && valor !== null && esPrimitivo(valor)) {
        limpio[clave] = valor;
      }
    });
    return limpio;
  }

  /**
   * Registra un evento del front, ya saneado.
   *
   * @param {Object} evento Lo que quiera quien llama; solo salen cuatro claves.
   * @param {function(Object): void} [salida] Dónde escribir. Inyectable para
   *        poder probarlo; por defecto, la consola del navegador.
   * @returns {Object} El evento saneado, para poder afirmarlo en los tests.
   */
  function traza(evento, salida) {
    const limpio = sanear(evento);
    const escribir =
      salida ||
      (typeof console !== "undefined" && console.info
        ? console.info.bind(console)
        : null);
    if (escribir) {
      escribir(limpio);
    }
    return limpio;
  }

  const Traza = {
    traza: traza,
    sanear: sanear,
    CLAVES_PERMITIDAS: CLAVES_PERMITIDAS,
  };

  if (typeof window !== "undefined") {
    window.Traza = Traza;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = Traza;
  }
})();
