// services/postventa-front/js/guarda_salida.js
// La guarda de salida del circuito (F-035, R78-R80). SOLO LEE el estado de
// appPostventa(): ni escribe, ni llama a sus métodos, ni red, ni almacenamiento.
//
// Desde el ajuste del 2026-10-05 todo el front navega en la misma pestaña,
// también desde `partes.html`. El circuito guarda la remesa en memoria (D4 de
// F-007; rehidratarla es F-021), así que salir con trabajo a medias lo pierde.
// Esta guarda lo evita con el `beforeunload` del navegador: pide confirmación
// SOLO cuando hay trabajo sin terminar (R79, `design.md` §16.15.2) y, si no,
// deja navegar sin preguntar. El texto del diálogo es el del navegador; lo que
// se pierde lo explica antes la leyenda de la barra (R47).
//
// No es un módulo del circuito ni lo modifica (R33, R81): lee su estado desde
// fuera con `Alpine.$data()` EN EL MOMENTO DE SALIR (Alpine va con `defer` y
// arranca después de este script) y compara con los selectores puros de
// `Pipeline` y las constantes de `Autoguardado`. Llamar a `pendientes()` o a
// `_autoguardado()` sería más corto, pero son métodos del componente y el
// segundo MONTA el autoguardado si no existía (R80).
//
// Falla abierta: si no puede leer el estado (sin Alpine, sin el componente o
// porque algo lanza), no pregunta. Sin componente no hay remesa que perder, y
// un diálogo «por si acaso» en cada salida enseña a aceptarlo sin leer.
//
// Patrón dual, como el resto de módulos: `window.GuardaSalida` en el navegador
// (y se instala sola) y `module.exports` para `node --test`.
(function () {
  "use strict";

  // Las fases de `js/app.js` en las que algo está en marcha (R79 a): trocear,
  // procesar y la tanda de archivar y cerrar. Un test estático comprueba que
  // `app.js` las sigue asignando con estos literales.
  const FASES_EN_MARCHA = Object.freeze(["troceando", "procesando", "archivando_y_cerrando"]);

  // El elemento que monta el componente del circuito en `partes.html`.
  const SELECTOR_CIRCUITO = '[x-data="appPostventa()"]';

  /**
   * R79 · ¿Tiene el circuito trabajo que se perdería al salir?
   *
   * Verdadero SI y solo SI se cumple alguna de las cuatro condiciones de
   * `design.md` §16.15.2 (D-15):
   *   (a) algo en marcha: una fase de FASES_EN_MARCHA o una tanda en curso;
   *   (b) correcciones sin guardar: el autoguardado guardando o con fallo;
   *   (c) algún parte ni cerrado (`parte.cerrado`) ni con estado rechazado o
   *       cerrado (`pipeline.estadoDe`);
   *   (d) un parte abierto que no está cerrado (cubre el rebote del
   *       autoguardado y el motivo escrito sin enviar).
   *
   * Los ficheros elegidos sin trocear (`seleccionado`) NO cuentan. Solo lee:
   * recorre `partes` por índice, sin llamar a nada del estado. Con un estado
   * ausente o raro devuelve false y nunca lanza.
   *
   * @param {object} estado El de `appPostventa()` (o null).
   * @param {object} pipeline `window.Pipeline` (inyectado para el test).
   * @param {object} autoguardado `window.Autoguardado` (ídem).
   * @returns {boolean}
   */
  function hayTrabajoSinTerminar(estado, pipeline, autoguardado) {
    try {
      if (!estado || typeof estado !== "object") {
        return false;
      }
      // (a) Algo en marcha.
      if (FASES_EN_MARCHA.indexOf(estado.fase) !== -1) {
        return true;
      }
      if (pipeline.hayTandaEnCurso() === true) {
        return true;
      }
      // (b) Correcciones sin guardar.
      const guardado = estado.estadoAutoguardado;
      if (guardado === autoguardado.GUARDANDO || guardado === autoguardado.FALLO) {
        return true;
      }
      // (d) Un parte abierto sin cerrar.
      const abierto = estado.parteAbierto;
      if (abierto && !abierto.cerrado) {
        return true;
      }
      // (c) Partes por terminar.
      const partes = estado.partes;
      if (!Array.isArray(partes)) {
        return false;
      }
      for (let i = 0; i < partes.length; i += 1) {
        const parte = partes[i];
        if (!parte || parte.cerrado) {
          continue;
        }
        const marca = pipeline.estadoDe(parte);
        if (marca !== pipeline.ESTADO_RECHAZADO && marca !== pipeline.ESTADO_CERRADO) {
          return true;
        }
      }
      return false;
    } catch (_error) {
      return false;
    }
  }

  /**
   * R80 · El estado del circuito, leído con la API pública de Alpine
   * (`Alpine.$data`), o null si no se puede: sin Alpine, sin `$data`, sin el
   * elemento o porque algo lanza. Nunca lanza.
   */
  function leerEstado(ventana, documento) {
    try {
      const alpine = ventana && ventana.Alpine;
      if (!alpine || typeof alpine.$data !== "function") {
        return null;
      }
      const elemento = documento.querySelector(SELECTOR_CIRCUITO);
      if (!elemento) {
        return null;
      }
      const estado = alpine.$data(elemento);
      return estado || null;
    } catch (_error) {
      return null;
    }
  }

  /**
   * R78 · El manejador de `beforeunload`. Con trabajo sin terminar pide
   * confirmación —`preventDefault()` y, para los navegadores que aún miran
   * `returnValue`, `returnValue = true` (la receta de MDN)— y devuelve true;
   * sin trabajo, o sin poder leer el estado, no toca el evento y devuelve
   * false.
   */
  function alSalir(evento, ventana, documento) {
    const estado = leerEstado(ventana, documento);
    if (!hayTrabajoSinTerminar(estado, ventana && ventana.Pipeline, ventana && ventana.Autoguardado)) {
      return false;
    }
    evento.preventDefault();
    evento.returnValue = true;
    return true;
  }

  /**
   * Registra UN `beforeunload` en la ventana, y nada más: ni clics, ni
   * `popstate`, ni temporizadores. `beforeunload` ya cubre todas las salidas
   * de la pestaña (enlaces, F5, cerrar, «Atrás», otra URL).
   */
  function instalar(ventana, documento) {
    ventana.addEventListener("beforeunload", function (evento) {
      alSalir(evento, ventana, documento);
    });
  }

  const GuardaSalida = {
    FASES_EN_MARCHA: FASES_EN_MARCHA,
    SELECTOR_CIRCUITO: SELECTOR_CIRCUITO,
    hayTrabajoSinTerminar: hayTrabajoSinTerminar,
    leerEstado: leerEstado,
    alSalir: alSalir,
    instalar: instalar,
  };

  if (typeof window !== "undefined") {
    window.GuardaSalida = GuardaSalida;
    instalar(window, document);
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = GuardaSalida;
  }
})();
