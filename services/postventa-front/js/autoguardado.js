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
//
// ---------------------------------------------------------------------------
// ENMIENDA · F-031, 2026-09-22 · `vaciarPendientes()` (R18, R20, R21, R22)
// ---------------------------------------------------------------------------
// Desde F-031 el backend **nombra el fichero archivado con los códigos que
// constan GUARDADOS** y coteja contra ellos los que vienen en el cuerpo de
// `POST /api/archivar`: si no cuadran, responde 409 y no archiva nada.
//
// Eso convierte el rebote de este módulo en parte del circuito de archivo.
// `requirements.md` §0.3 tiene medida la ventana: corregir un código de obra y
// pulsar «archivar y cerrar» antes de los 1.500 ms —o con la petición de
// guardado todavía en vuelo— mandaría al backend un código que aún no está en
// la base. `hayPendiente` ya existía desde F-026 y **no lo llamaba nadie**.
//
// `vaciarPendientes()` es lo que cierra esa ventana: fuerza lo escrito y sin
// guardar de **cualquier** parte y **espera** a que termine. Lo llama
// `js/app.js` en `confirmarArchivo`, antes de calcular la tanda.
//
// Lo que la enmienda NO cambia: ni el rebote, ni el criterio de «hay cambios»,
// ni el respeto por `parte.ediciones` (R21, que es F-026 R52 dicho otra vez),
// ni la ignorancia del módulo sobre veredictos y estados (F-026 R55). El
// vaciado es una forma de **adelantar** el guardado que ya iba a ocurrir, no
// una segunda forma de guardar.

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

  /**
   * Lo que se le dice a quien pulsa «archivar y cerrar» con correcciones sin
   * guardar que no han podido guardarse (F-031 R20).
   *
   * Añade **lo único** que `MENSAJE_FALLO` no podía decir —que la tanda no ha
   * salido— y reutiliza el resto. Dos explicaciones distintas del mismo hecho
   * es lo que hace que no se lea ninguna.
   *
   * Vive aquí y no en `app.js` por lo mismo que `AVISO_CADUCADA` vive en
   * `js/confirmacion.js`: `app.js` es la única habitación de la casa sin tests.
   */
  const AVISO_SIN_GUARDAR =
    "No se ha archivado nada: quedan correcciones sin guardar. " + MENSAJE_FALLO;

  /**
   * Cuántas veces reintenta `vaciarPendientes` antes de rendirse.
   *
   * Hay tope a propósito: `disparar` se reprograma cuando encuentra otro
   * guardado en vuelo, así que un bucle sin tope podría no terminar nunca con
   * alguien tecleando delante. Tres rondas es el guardado que se está
   * esperando, más dos reintentos; pasadas, se devuelve `{ok:false}` y la
   * tanda no se lanza, que es lo que hay que hacer de todas formas.
   */
  const RONDAS_DE_VACIADO = 3;

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
    /**
     * F-031 R18 · el parte al que pertenece cada hash con algo escrito.
     *
     * `pendientes` guarda **valores**, y para guardarlos hace falta el parte
     * entero: `guardar` es `revalidarYGuardar`, que necesita sus bytes y su
     * extracción. Hasta F-031 bastaba con el parte que venía en la pulsación,
     * porque siempre se guardaba el que se acababa de teclear; el vaciado
     * tiene que poder guardar el de **cualquiera**, incluido uno cuyo guardado
     * se cayó hace dos partes.
     */
    const partesConPendiente = {};

    let temporizador = null;
    let parteEnEspera = null;
    let enVuelo = false;
    /**
     * La promesa del guardado en vuelo, o `null`.
     *
     * F-026 solo necesitaba la bandera `enVuelo` —«¿hay uno en el aire?»—;
     * F-031 necesita además poder **esperarlo**, y una bandera no se espera.
     */
    let promesaEnVuelo = null;
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

      const cadena = Promise.resolve()
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
          delete partesConPendiente[parte.hash];
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
          promesaEnVuelo = null;
          return resultado;
        });

      // F-031 R18 · se conserva para poder esperarla. La asignación va aquí,
      // fuera de la cadena: el último `.then` corre en una microtarea
      // posterior, así que cuando `disparar` devuelve, la promesa ya está
      // puesta y quien la espere la encuentra.
      promesaEnVuelo = cadena;
      return cadena;
    }

    /** Los hashes que tienen algo distinto de lo guardado (F-031 R18, R22). */
    function hashesConCambios() {
      return Object.keys(pendientes).filter(hayCambios);
    }

    /**
     * F-031 R18 · fuerza lo que esté escrito y sin guardar, y espera.
     *
     * El orden importa y es el de `design.md` §6.1:
     *
     *   1. se espera al guardado **en vuelo**, si lo hay. Lanzar otro encima
     *      escribiría dos veces lo mismo contra la base compartida y dejaría
     *      en ella el veredicto de la carrera que ganara;
     *   2. se retira el rebote en espera y se dispara lo que quede pendiente,
     *      de **todos** los partes, esperando a cada uno;
     *   3. como mucho `RONDAS_DE_VACIADO` rondas.
     *
     * No toca `parte.ediciones` (R21) ni dispara nada cuando no hay cambios
     * (R22): las dos cosas salen de reutilizar `hayCambios` y `disparar` tal y
     * como F-026 los dejó, en vez de escribir aquí un segundo criterio.
     *
     * @returns {Promise<{ok: boolean, motivo: string}>} `ok` falso cuando al
     *          acabar SIGUE quedando algo sin guardar. `app.js` no lanza la
     *          tanda con eso (R20).
     */
    async function vaciarPendientes() {
      for (let ronda = 0; ronda < RONDAS_DE_VACIADO; ronda += 1) {
        if (promesaEnVuelo) {
          await promesaEnVuelo;
        }

        const hashes = hashesConCambios();
        if (hashes.length === 0) {
          return { ok: true, motivo: "sin_pendientes" };
        }

        // El rebote en espera se retira: si saltara después, escribiría contra
        // una remesa que la tanda ya habrá archivado.
        cancelarPendiente();

        for (const hash of hashes) {
          const parte = partesConPendiente[hash];
          if (!parte) {
            // No debería ocurrir: lo pendiente solo nace en `alEscribir`, que
            // apunta el parte. Si ocurriera, se prefiere no archivar —eso lo
            // decide la comprobación final— a inventarse un parte.
            continue;
          }
          // `disparar` no lanza: cuando el guardado se cae, lo publica como
          // fallo y deja lo pendiente donde estaba, que es justo lo que hace
          // falta para reintentar en la ronda siguiente (R21).
          await disparar(parte);
        }
      }

      if (promesaEnVuelo) {
        await promesaEnVuelo;
      }
      if (hashesConCambios().length === 0) {
        return { ok: true, motivo: "vaciado" };
      }
      return { ok: false, motivo: "quedan_cambios_sin_guardar" };
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
        // F-031 R18 · con qué parte se guarda esto, el día que lo fuerce el
        // vaciado y no la pausa.
        partesConPendiente[parte.hash] = parte;

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
        delete partesConPendiente[parte.hash];
      },

      /** F-031 R18 · fuerza lo escrito y sin guardar, y espera. Ver arriba. */
      vaciarPendientes: vaciarPendientes,

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
    AVISO_SIN_GUARDAR: AVISO_SIN_GUARDAR,
    RONDAS_DE_VACIADO: RONDAS_DE_VACIADO,
    crearAutoguardado: crearAutoguardado,
  };

  if (typeof window !== "undefined") {
    window.Autoguardado = Autoguardado;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = Autoguardado;
  }
})();
