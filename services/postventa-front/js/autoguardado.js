// services/postventa-front/js/autoguardado.js
// F-026 R50-R55 · Guardar lo que se escribe, según se escribe, sin botón.
//
// El defecto que cierra este módulo es concreto: hasta F-026, `editarCampo`
// dejaba la corrección **solo en memoria** y quien escribía y se iba la
// perdía. Persistir existía, pero solo por acción explícita —el botón
// «Revalidar»—, y quien no lo pulsaba no se enteraba de nada.
//
// Lógica pura, como `js/confirmacion.js`: sin DOM, sin Alpine y **sin reloj
// propio**. El temporizador entra por parámetro. Sin eso, probar «una pausa»
// costaría segundos de espera real por test, y el rebote —que es justo lo que
// protege a la base compartida— se quedaría sin comprobar.
//
// Las tres cosas que este módulo decide, y por qué:
//
//   1. **Cuándo guardar** (R51): una pausa desde la última pulsación, no una
//      pulsación. Lo que se dispara son DOS peticiones, y la segunda escribe
//      en un PostgreSQL que comparten otros dos proyectos en producción.
//   2. **Si hay algo que guardar** (R51): solo si el valor cambió respecto a
//      lo último guardado. Escribir una letra y borrarla no es un cambio.
//   3. **Qué se enseña** (R52): guardando, guardado, y **no se ha podido
//      guardar**. El tercero es el que importa y **no se va solo**: quien
//      escribe y no ve nada supone que se guardó.
//
// Lo que este módulo NO hace, a propósito:
//
//   - **No compone peticiones.** Qué se pide y en qué orden vive en
//     `js/pipeline.js`. Aquí solo se llama al `guardar` que le pasen, que en
//     `app.js` es `revalidarYGuardar` (R50): guardar sin revalidar dejaría en
//     la base el veredicto que la IA emitió sobre el dato **sin corregir**.
//   - **No mira el veredicto** (R55). Ni lo recibe. Perder lo escrito es igual
//     de malo en un parte verde, así que no hay forma de que este módulo deje
//     fuera a nadie.
//   - **No toca `parte.ediciones`** (R52, R53). Lo que la persona escribió se
//     queda donde está pase lo que pase con la petición, y lo que leyó la IA
//     sigue intacto en `parte.extraccion` para que F-015 pueda evaluar el
//     prompt contra lo que dijo el modelo, no contra lo que corrigió alguien.
//
// El módulo se expone en las dos direcciones: `window` para el navegador y
// `module.exports` para `node --test`. Cero herramientas de build.

(function () {
  "use strict";

  /** Los tres estados de R52, más el de «aquí no ha pasado nada todavía». */
  const INACTIVO = "";
  const GUARDANDO = "guardando";
  const GUARDADO = "guardado";
  const FALLO = "fallo";

  /**
   * Lo que se le dice a quien escribe cuando el guardado falla (R52).
   *
   * Dice las dos cosas que necesita saber: que **no** está guardado, y que lo
   * que escribió **sigue ahí**. Sin la segunda, lo razonable es volver a
   * teclearlo todo, o peor, cerrar y dar por perdido lo que no se ha perdido.
   */
  const MENSAJE_FALLO =
    "No se ha podido guardar la corrección. Lo que has escrito sigue en " +
    "pantalla: vuelve a escribir algo o pulsa «Revalidar» para reintentarlo.";

  /** Mismo criterio que `js/pipeline.js::normalizarValor`. */
  function normalizar(valor) {
    if (valor === undefined || valor === null) {
      return "";
    }
    return String(valor).trim();
  }

  /**
   * ¿Este valor es distinto del que se guardó?
   *
   * Se compara **normalizado** porque normalizado es como viaja: `pipeline.js`
   * recorta los espacios y convierte el vacío en `null` antes de enviar. Un
   * espacio de sobra al final no cambia ni un byte de lo que se escribiría en
   * la base, así que no justifica una petición contra una base compartida.
   */
  function esCambio(guardado, valor) {
    return normalizar(guardado) !== normalizar(valor);
  }

  /**
   * Monta un autoguardado.
   *
   * @param {object} ajustes
   * @param {number} ajustes.retardoMs Milisegundos de pausa antes de guardar.
   *        Obligatorio y mayor que cero: vive en `js/config.js`, con la razón
   *        del número escrita al lado.
   * @param {function} ajustes.guardar `(parte) => Promise`. En `app.js` es
   *        `revalidarYGuardar` (R50). Si la promesa se rompe, es un fallo de
   *        guardado y se dice (R52).
   * @param {function} [ajustes.alCambiarEstado] `({estado, mensaje, parte})`.
   *        Por aquí sale lo que se pinta; el módulo no conoce la pantalla.
   * @param {function} [ajustes.programar] `(fn, ms) => id`. Por defecto
   *        `setTimeout`.
   * @param {function} [ajustes.cancelar] `(id) => void`. Por defecto
   *        `clearTimeout`.
   */
  function crearAutoguardado(ajustes) {
    const opciones = ajustes || {};
    const retardoMs = opciones.retardoMs;
    const guardar = opciones.guardar;

    if (typeof retardoMs !== "number" || !Number.isFinite(retardoMs) || retardoMs <= 0) {
      // Sin retardo no hay pausa: sería una escritura por tecla contra una
      // base compartida. Se falla al montar, que es cuando se puede ver, y no
      // en producción cuando la base empieza a ir despacio.
      throw new Error(
        `el autoguardado necesita un retardo en milisegundos mayor que cero, y recibió ${retardoMs}`,
      );
    }
    if (typeof guardar !== "function") {
      throw new Error("el autoguardado necesita una función `guardar`");
    }

    const programar =
      opciones.programar ||
      function (fn, ms) {
        return setTimeout(fn, ms);
      };
    const cancelar =
      opciones.cancelar ||
      function (id) {
        clearTimeout(id);
      };
    const alCambiarEstado = opciones.alCambiarEstado || function () {};

    /** Lo último que consta guardado de cada parte: `{hash: {campo: valor}}`. */
    const guardados = {};
    /** Lo escrito y aún no guardado: `{hash: {campo: valor}}`. */
    const pendientes = {};

    let temporizador = null;
    let parteEnEspera = null;
    let enVuelo = false;
    let estado = INACTIVO;
    let mensaje = "";

    function publicar(nuevoEstado, nuevoMensaje, parte) {
      estado = nuevoEstado;
      mensaje = nuevoMensaje;
      alCambiarEstado({ estado: estado, mensaje: mensaje, parte: parte });
    }

    function cancelarPendiente() {
      if (temporizador !== null) {
        cancelar(temporizador);
        temporizador = null;
      }
      parteEnEspera = null;
    }

    /**
     * ¿Queda algo distinto de lo guardado en lo que se ha escrito?
     *
     * Se mira el conjunto y no el campo que se acaba de teclear, porque un
     * guardado los lleva todos: si alguien corrige `unidad` y luego deshace
     * `observaciones`, lo que decide es si queda ALGO distinto.
     */
    function hayCambios(hash) {
      const escrito = pendientes[hash] || {};
      const guardado = guardados[hash] || {};
      return Object.keys(escrito).some(function (nombre) {
        return esCambio(guardado[nombre], escrito[nombre]);
      });
    }

    function disparar(parte) {
      temporizador = null;
      parteEnEspera = null;

      if (enVuelo) {
        // Ya hay un guardado en el aire. Lanzar otro encima sería escribir dos
        // veces lo mismo y, peor, dejar en la base el veredicto de la carrera
        // que ganara. Se vuelve a esperar la pausa.
        return programarGuardado(parte);
      }
      if (!hayCambios(parte.hash)) {
        return Promise.resolve();
      }

      enVuelo = true;
      publicar(GUARDANDO, "Guardando…", parte);

      return Promise.resolve()
        .then(function () {
          return guardar(parte);
        })
        .then(function () {
          // Lo pendiente pasa a ser lo guardado. `app.js` vuelve a fijar estos
          // valores con los suyos al anotar el guardado; las dos fuentes dicen
          // lo mismo y la segunda es la autoritativa.
          guardados[parte.hash] = Object.assign(
            {},
            guardados[parte.hash] || {},
            pendientes[parte.hash] || {},
          );
          delete pendientes[parte.hash];
          publicar(GUARDADO, "Guardado.", parte);
        })
        .catch(function (error) {
          // R52 · lo pendiente NO se tira: sigue en pantalla y sigue pendiente,
          // así que la siguiente pausa lo reintenta. Y el aviso se queda
          // puesto hasta que un guardado salga bien: no hay temporizador que
          // lo borre, porque un aviso que se va solo es un aviso que nadie
          // llega a leer.
          publicar(FALLO, MENSAJE_FALLO, parte);
          return { error: error };
        })
        .then(function (resultado) {
          enVuelo = false;
          return resultado;
        });
    }

    function programarGuardado(parte) {
      cancelarPendiente();
      parteEnEspera = parte;
      temporizador = programar(function () {
        return disparar(parte);
      }, retardoMs);
      return Promise.resolve();
    }

    return {
      /**
       * Una pulsación en un campo.
       *
       * @returns {{programado: boolean, motivo: string}} `programado` es falso
       *          cuando lo escrito coincide con lo guardado: no hay nada que
       *          escribir en la base.
       */
      alEscribir(parte, nombre, valor) {
        if (!parte || !parte.hash) {
          return { programado: false, motivo: "sin_parte" };
        }

        // Cambiar de parte con una corrección a medias **guarda** la del parte
        // anterior en vez de tirarla: lo escrito no se pierde por abrir otro
        // papel, que es el defecto que R50 viene a cerrar.
        if (parteEnEspera && parteEnEspera.hash !== parte.hash) {
          const anterior = parteEnEspera;
          cancelarPendiente();
          disparar(anterior);
        }

        const escrito = pendientes[parte.hash] || {};
        escrito[nombre] = valor;
        pendientes[parte.hash] = escrito;

        if (!hayCambios(parte.hash)) {
          // Se escribió lo mismo que ya consta guardado (o se deshizo lo
          // tecleado). No hay nada que guardar, y lo que hubiera programado
          // antes deja de tener sentido.
          cancelarPendiente();
          return { programado: false, motivo: "sin_cambios" };
        }

        programarGuardado(parte);
        return { programado: true, motivo: "programado" };
      },

      /**
       * Lo que consta guardado de un parte, después de un guardado correcto.
       *
       * Lo llama `app.js` desde `_anotarGuardado`, o sea en los tres sitios
       * donde un parte se guarda: al procesarlo, al revalidarlo a mano y al
       * autoguardarlo. Sin esto, el módulo no tendría contra qué comparar y la
       * primera pulsación de cada parte guardaría aunque no cambiara nada.
       */
      anotarGuardado(parte, valores) {
        if (!parte || !parte.hash) {
          return;
        }
        guardados[parte.hash] = Object.assign({}, valores || {});
        delete pendientes[parte.hash];
      },

      /** Cancela lo que hubiera en espera. Al reiniciar, o al cerrar la remesa. */
      cancelarPendiente: cancelarPendiente,

      /** ¿Queda algo escrito sin guardar de este parte? */
      hayPendiente(parte) {
        return Boolean(parte && parte.hash && hayCambios(parte.hash));
      },

      /** El estado de R52, para que la pantalla lo pinte. */
      estado() {
        return estado;
      },

      /** El texto que acompaña al estado. */
      mensaje() {
        return mensaje;
      },
    };
  }

  const Autoguardado = {
    INACTIVO: INACTIVO,
    GUARDANDO: GUARDANDO,
    GUARDADO: GUARDADO,
    FALLO: FALLO,
    MENSAJE_FALLO: MENSAJE_FALLO,
    crearAutoguardado: crearAutoguardado,
  };

  if (typeof window !== "undefined") {
    window.Autoguardado = Autoguardado;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = Autoguardado;
  }
})();
