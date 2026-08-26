// services/postventa-front/js/confirmacion.js
// R19 · Confirmación explícita en dos pasos antes de archivar. Lógica pura:
// sin DOM, sin Alpine, sin reloj propio —el instante entra por parámetro—.
//
// Por qué existe este módulo y no es un booleano en `js/app.js`: archivar
// dispara una TANDA DE SUBIDAS REALES a SharePoint, una por parte apto. La
// diferencia entre eso y un clic accidental es exactamente lo que hay aquí
// dentro, y `app.js` es la única habitación de la casa sin tests
// (`design.md` §3). Vivía ahí hasta la review de F-007, donde se vio que no
// lo comprobaba nada.
//
// El estado es un objeto plano —`{armadaEn}`— o `null`, y NUNCA se muta: se
// reasigna. Así Alpine ve el cambio sin depender de que haga proxy profundo
// de un objeto con métodos dentro.
//
// El módulo se expone en las dos direcciones: `window` para el navegador y
// `module.exports` para `node --test`. Cero herramientas de build.

(function () {
  "use strict";

  /**
   * Cuánto vale una confirmación antes de caducar, en milisegundos.
   *
   * Un minuto: sobra para leer «se subirán a SharePoint» y decidir, y no deja
   * la pantalla armada mientras el usuario se va a comer. Sin caducidad, un
   * clic al volver subiría la remesa entera sin que nadie haya confirmado
   * nada en ese momento.
   */
  const VENTANA_MS = 60000;

  /** Motivos por los que un segundo clic puede no disparar. */
  const SIN_ARMAR = "sin_armar";
  const CADUCADA = "caducada";

  /** Texto para el usuario cuando la confirmación se le pasó de tiempo. */
  const AVISO_CADUCADA =
    "La confirmación caducó. Vuelve a pulsar «Archivar los partes aptos».";

  /** El mismo aviso para el cierre en Sigrid (F-009 R15). */
  const AVISO_CADUCADA_CIERRE =
    "La confirmación caducó. Vuelve a pulsar «Cerrar las incidencias».";

  /**
   * El aviso de caducidad de una acción concreta.
   *
   * Existe porque F-009 reutiliza este módulo **tal cual** —la caducidad, el
   * doble clic y el reloj hacia atrás son el mismo problema— pero el texto que
   * ve el usuario tiene que nombrar el botón que va a volver a pulsar. Un
   * aviso que le mande a otro sitio es peor que no ponerlo.
   *
   * Los dos textos viven aquí y no en `app.js` por lo mismo que el resto del
   * módulo: `app.js` es la única habitación de la casa sin tests.
   */
  function avisoCaducada(accion) {
    return accion === "cierre" ? AVISO_CADUCADA_CIERRE : AVISO_CADUCADA;
  }

  function esInstante(valor) {
    return typeof valor === "number" && Number.isFinite(valor);
  }

  /**
   * Primer clic: arma la confirmación.
   *
   * @param {number} ahoraMs Instante en milisegundos (`Date.now()`).
   * @returns {{armadaEn: number}} El estado armado, para guardarlo en la vista.
   */
  function armar(ahoraMs) {
    if (!esInstante(ahoraMs)) {
      // Sin reloj válido no hay caducidad posible, y una confirmación que no
      // caduca nunca es justo lo que este módulo viene a evitar. Se lanza en
      // vez de asumir un instante: fallar ruidoso, no archivar a ciegas.
      throw new Error(`armar necesita un reloj en milisegundos, y recibió ${ahoraMs}`);
    }
    return { armadaEn: ahoraMs };
  }

  /**
   * ¿Hay que pintar el «¿Seguro?» en pantalla?
   *
   * NO mira el reloj a propósito: el reloj no es reactivo y el panel no se
   * cerraría solo al caducar. La caducidad la descubre el clic, en `resolver`.
   *
   * @param {{armadaEn: number}|null} estado
   * @returns {boolean}
   */
  function pendiente(estado) {
    return Boolean(estado) && esInstante(estado.armadaEn);
  }

  /**
   * Segundo clic: decide si se dispara de verdad.
   *
   * @param {{armadaEn: number}|null} estado El estado guardado en la vista.
   * @param {number} ahoraMs Instante del clic.
   * @param {number} [ventanaMs] Ventana de validez. Por defecto `VENTANA_MS`.
   * @returns {{dispara: boolean, estado: null, motivo: string}}
   *          `estado` es SIEMPRE `null`: pase lo que pase, este armado queda
   *          consumido. Es la defensa contra el doble clic sobre «Sí,
   *          archivar», que si no dispararía dos tandas de subidas.
   */
  function resolver(estado, ahoraMs, ventanaMs) {
    const ventana = ventanaMs === undefined ? VENTANA_MS : ventanaMs;

    if (!pendiente(estado)) {
      // Un solo clic no sube nada a ninguna parte.
      return { dispara: false, estado: null, motivo: SIN_ARMAR };
    }

    const transcurrido = esInstante(ahoraMs) ? ahoraMs - estado.armadaEn : Infinity;

    // `transcurrido < 0` es un reloj que ha saltado hacia atrás (cambio de
    // hora, sincronización). Ante la duda, no se archiva.
    if (transcurrido < 0 || transcurrido > ventana) {
      return { dispara: false, estado: null, motivo: CADUCADA };
    }

    return { dispara: true, estado: null, motivo: "" };
  }

  /** Cancelar: vuelve al estado inicial. */
  function cancelar() {
    return null;
  }

  const Confirmacion = {
    VENTANA_MS: VENTANA_MS,
    SIN_ARMAR: SIN_ARMAR,
    CADUCADA: CADUCADA,
    AVISO_CADUCADA: AVISO_CADUCADA,
    AVISO_CADUCADA_CIERRE: AVISO_CADUCADA_CIERRE,
    avisoCaducada: avisoCaducada,
    armar: armar,
    pendiente: pendiente,
    resolver: resolver,
    cancelar: cancelar,
  };

  if (typeof window !== "undefined") {
    window.Confirmacion = Confirmacion;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = Confirmacion;
  }
})();
