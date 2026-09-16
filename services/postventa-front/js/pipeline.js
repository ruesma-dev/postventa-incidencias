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

  // ---------------------------------------------------------------------
  // Enmienda del 2026-09-16 · F-028 T18
  // ---------------------------------------------------------------------
  // Aquí vivía `MOTIVOS_APROBABLES`, copia de
  // `domain/models/aprobacion.py::MOTIVOS_APROBABLES`, y con él `esAprobable`
  // y `cuerpoDeAprobacion`.
  //
  // Se van los tres porque F-028 **deroga la pregunta**: una persona puede
  // mover a `aprobado` o a `rechazado` cualquier parte que no esté `cerrado`
  // (R9, R10), venga el veredicto de donde venga. T15 ya retiró `es_aprobable`
  // del dominio por lo mismo.
  //
  // Y dejarlos vivos no era neutral: `esAprobable` escondía el gesto en los
  // partes **aptos**, que son justo los que esta feature existe para poder
  // rechazar antes de que se archiven.
  //
  // Su sustituto es `cuerpoDeCambioDeEstado`, que no pregunta si el parte es
  // aprobable y sí exige lo que hace que la decisión signifique algo: los dos
  // destinos manuales, quién decide, el motivo al rechazar y la remesa.

  /**
   * F-028 · los CUATRO estados de un parte, tal y como los nombra el backend
   * (`domain/models/estado.py::EstadoParte`).
   *
   * Aquí no se deriva ninguno (R17): el estado lo manda el backend en el bloque
   * `estado` de `/api/parte` y `/api/estado`, y la pantalla lo pinta. Estos
   * literales están para **comparar** lo que llega, no para calcularlo.
   *
   * > Enmienda del 2026-09-16 · F-028 T17. Aquí vivía `APROBACION_VIGENTE`, de
   * > F-026: el front miraba si la aprobación seguía en pie comparando su
   * > destino con el de la validación de ahora. Eso se va entero —la caducidad
   * > la resuelve el backend al derivar (R19), y la pantalla no recomputa nada—
   * > y con ello se va también `aprobacionVale`.
   */
  const ESTADO_APROBADO = "aprobado";
  const ESTADO_PENDIENTE = "pendiente";
  const ESTADO_CERRADO = "cerrado";

  /**
   * F-028 R38, R39 · las CUATRO marcas de la pantalla, y por qué son cinco
   * literales.
   *
   * `pendiente` se pinta ámbar o rojo —es la única lectura del veredicto que
   * queda, y es un matiz de color— y `aprobado` se pinta de dos maneras:
   * **verde liso** si lo dio por bueno la máquina y **verde con anillo** si lo
   * dio por bueno una persona. Esa segunda distinción es R39 y es medio motivo
   * de que F-026 existiera: uno lo aprobó el veredicto y el otro lo aprobó
   * alguien **a pesar** del veredicto, y pintarlos igual borra ese dato.
   *
   * `rechazado` y `cerrado` son marcas propias: un rechazado no puede parecer
   * «pendiente de mirar» —ya lo miró alguien— y un cerrado no admite ningún
   * gesto (R41).
   */
  const SEMAFORO_APROBADO = "aprobado";
  const SEMAFORO_VERDE = "verde";
  const SEMAFORO_AMBAR = "ambar";
  const SEMAFORO_ROJO = "rojo";
  const SEMAFORO_RECHAZADO = "rechazado";
  const SEMAFORO_CERRADO = "cerrado";
  const SIN_MARCA = "";

  /**
   * F-028 R10 · los DOS destinos que una persona puede pedir, y no hay más.
   *
   * Copia de `interface_adapters/api/estado.py::ESTADOS_MANUALES`. A
   * `pendiente` no se vuelve a mano —es donde nace lo que nadie ha mirado— y a
   * `cerrado` solo se llega cerrando la incidencia en el ERP, que es otra cosa
   * y tiene su propio circuito.
   */
  const ESTADOS_MANUALES = ["aprobado", "rechazado"];

  /**
   * F-028 R13 · lo que mide un motivo como mucho.
   *
   * Copia de `domain/models/estado.py::LIMITE_MOTIVO`, igual que
   * `UMBRAL_CONFIANZA` y `CAMPOS_DEL_PARTE` son copias de sus constantes del
   * dominio. El backend lo aplica igual; tenerlo aquí es lo que permite decir
   * «te has pasado» con el texto delante, en vez de mandarlo y recibir un 400.
   */
  const LIMITE_MOTIVO = 500;

  /** F-028 R11 · el estado cuyo motivo es obligatorio. */
  const ESTADO_RECHAZADO = "rechazado";

  /**
   * F-028 R43 · lo que se le dice a quien revisa cuando su decisión caducó.
   *
   * **Es un hecho, no una acusación.** Dice que el veredicto cambió —que es lo
   * que pasó— y no que nadie hiciera nada mal: quien corrigió un campo estaba
   * haciendo justo lo que la pantalla le pide, y lo que ocurre después es una
   * consecuencia del diseño (R19), no un error suyo.
   */
  const AVISO_DECISION_CADUCADA =
    "La decisión que había tomado una persona sobre este parte dejó de " +
    "contar: el veredicto ha cambiado al revalidar, así que hay que volver " +
    "a decidir sobre el veredicto nuevo.";

  /** Lo que `/api/archivar` acepta, además del fichero. NADA personal (R29). */
  const CAMPOS_DE_ARCHIVO = [
    "hash",
    "codigo_obra",
    "numero_incidencia",
    "veredicto",
    "destino",
  ];

  /** Lo que se le dice al usuario cuando la remesa no se pudo registrar. */
  const AVISO_SIN_REMESA =
    "no se ha podido registrar la remesa, así que los partes no se podrán " +
    "archivar: ";

  const VEREDICTO_APTO = "apto";
  const DESTINO_ARCHIVO = "archivo_y_cierre";

  // F-009 · el estado del archivo que el backend exige para poder cerrar.
  // Es el mismo valor que declara `EstadoArchivo` en el dominio: si algun
  // dia cambia alli, el backend responde 400 diciendo cual es el admitido,
  // en vez de aceptar algo que no entiende.
  const ESTADO_ARCHIVADO = "archivado";
  const DESTINO_COLA = "cola_validacion_humana";
  const DESTINO_REVISION = "revision_manual";

  // F-025 · el estado del gráfico que significa «el parte ESTÁ dentro de
  // Sigrid». El literal vive aquí y en un solo sitio: lo leen `estaAdjuntado`
  // —lo que decide si se pide el cierre— y el circuito de la tanda, y dos
  // copias de la misma cadena divergen el día que el backend la cambie.
  const ESTADO_ADJUNTADO = "adjuntado";

  // F-025 R13 · los tres pasos, tal y como se publican por `alPaso`. Son lo
  // que la pantalla enseña por parte mientras la tanda corre: con la
  // confirmación única, entre pulsar y terminar hay ~20 s por parte y un botón
  // quieto invita a pulsarlo otra vez.
  const PASO_ARCHIVANDO = "archivando";
  const PASO_ADJUNTANDO = "adjuntando";
  const PASO_CERRANDO = "cerrando";

  /** F-025 R21 · lo que se dice cuando la ventana del ERP está cerrada. */
  const MENSAJE_ERP_CERRADO =
    "archivado; no se ha pedido nada al ERP porque su ventana de escritura " +
    "está cerrada";

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

  /**
   * F-028 · el estado que el backend dice de este parte, o cadena vacía.
   *
   * `parte.estadoParte` es el bloque `estado` tal y como viene de
   * `POST /api/parte` y `POST /api/estado`. Se llama así y no `parte.estado`
   * porque en `js/app.js` ese nombre lleva desde F-007 la **fase** del parte en
   * pantalla —«leyendo», «listo», «error»—, y dos cosas distintas con el mismo
   * nombre en el mismo objeto son un fallo esperando a que alguien las
   * confunda.
   *
   * Devuelve `""` —y no `null`— cuando no consta: así el llamante compara
   * contra un literal y no tiene que distinguir tres formas de «no hay».
   */
  function estadoDe(parte) {
    const bloque = parte && parte.estadoParte;
    return (bloque && bloque.estado) || SIN_MARCA;
  }

  /**
   * F-028 R43 · ¿la decisión de una persona ha dejado de contar?
   *
   * R43 pide distinguir dos hechos: «lo decidió una persona» y «el veredicto
   * cambió y la decisión dejó de contar». El primero lo dice el propio bloque
   * —`decidido_por_persona`—; el segundo **no se puede leer de una sola
   * respuesta**, y ahí está el problema: cuando una aprobación caduca (R19), el
   * backend deja de firmarla y lo que llega es un bloque con
   * `decidido_por_persona: false`, idéntico al de un parte que nunca miró
   * nadie.
   *
   * Lo que sí distingue los dos casos es **el par de respuestas consecutivas**:
   * había una decisión firmada y, después de revalidar, ya no la hay. Eso es lo
   * que compara esta función, y por eso vive aquí y no en `js/app.js`: comparar
   * dos bloques es una decisión, y las decisiones se prueban.
   *
   * Esto **no deriva ningún estado** (R17): los dos bloques vienen del backend
   * tal cual y aquí no se calcula ninguno, solo se mira si la firma se ha
   * perdido por el camino.
   *
   * Callarse es el caso normal, y hay tres formas de llegar a él: que la
   * decisión siga firmada, que nunca la hubiera, y que no haya bloque nuevo
   * —un guardado fallido no sabe nada del estado, y decir que la decisión
   * caducó sería afirmar algo que nadie ha comprobado—.
   *
   * @param {object} anterior El bloque `estado` que tenía el parte.
   * @param {object} nuevo El que acaba de devolver el backend.
   * @returns {string} El aviso de R43, o cadena vacía si no hay nada que decir.
   */
  function avisoDeEstado(anterior, nuevo) {
    const habia = Boolean(anterior && anterior.decidido_por_persona);
    const sigue = Boolean(nuevo && nuevo.decidido_por_persona);
    if (habia && !sigue && nuevo) {
      return AVISO_DECISION_CADUCADA;
    }
    return SIN_MARCA;
  }

  /**
   * F-028 R38, R39 · la marca de este parte, a partir de **su estado**.
   *
   * **El estado lo manda el backend y aquí solo se pinta** (R17). Hasta F-026
   * esta función derivaba el color del veredicto y de la aprobación; ahora
   * decide por el estado, y la validación sirve para una sola cosa: elegir
   * entre ámbar y rojo **dentro** de `pendiente`.
   *
   * No es un cambio cosmético. Mientras el color saliera del veredicto, un
   * parte apto que una persona había rechazado se pintaba **verde**, que es
   * exactamente el defecto que abre esta feature.
   *
   * Y por eso **sin bloque de estado no se pinta nada**: un parte cuyo guardado
   * falló no tiene estado conocido, y pintarlo verde porque su veredicto es
   * apto sería afirmar que está aprobado sin haberlo preguntado. El fallo se va
   * al lado seguro —sin marca, nunca con la de aprobado—, que es el mismo
   * criterio que aplica el dominio cuando le faltan las dos mitades de la
   * huella.
   *
   * @param {object} validacion El veredicto de `/api/validar`.
   * @param {object} estado El bloque `estado` del backend, o `null`.
   */
  function semaforoDe(validacion, estado) {
    const cual = (estado && estado.estado) || SIN_MARCA;
    if (cual === ESTADO_APROBADO) {
      // R39 · la única distinción que no sale del estado, sino de quién lo
      // decidió. El anillo es lo que separa «lo dio por bueno la máquina» de
      // «alguien se hizo responsable a pesar de la máquina».
      return estado.decidido_por_persona ? SEMAFORO_APROBADO : SEMAFORO_VERDE;
    }
    if (cual === SEMAFORO_RECHAZADO) {
      return SEMAFORO_RECHAZADO;
    }
    if (cual === ESTADO_CERRADO) {
      return SEMAFORO_CERRADO;
    }
    if (cual === ESTADO_PENDIENTE) {
      if (validacion && validacion.destino === DESTINO_COLA) {
        return SEMAFORO_AMBAR;
      }
      if (validacion && validacion.destino === DESTINO_REVISION) {
        return SEMAFORO_ROJO;
      }
    }
    return SIN_MARCA;
  }

  /** ¿Este parte se puede archivar? Apto Y con destino de archivo (R21). */
  function esArchivable(validacion) {
    return Boolean(
      validacion &&
        validacion.veredicto === VEREDICTO_APTO &&
        validacion.destino === DESTINO_ARCHIVO,
    );
  }

  /**
   * F-028 R33 · ¿entra este parte en el circuito de archivo, gráfico y cierre?
   *
   * **Un solo camino**: que su estado sea `aprobado`. Ni dos, ni el atajo del
   * apto. Es el mismo criterio que aplican las tres puertas del backend desde
   * T11 —`estado_del_parte(...) is EstadoParte.APROBADO`— y se comprueba allí
   * otra vez, leyendo el almacén; esto evita que la tanda intente lo que va a
   * responder 409.
   *
   * Lo que esto arregla, y es medio encargo de la feature: hasta F-028 un parte
   * **apto** entraba en el circuito aunque una persona lo hubiera rechazado,
   * porque el criterio de la pantalla era el veredicto. Ahora un rechazado no
   * circula aunque la máquina lo hubiera dado por bueno, y un no apto **sí**
   * circula si alguien lo aprobó (R9).
   *
   * Y el `cerrado` queda fuera por la misma regla, sin necesidad de un caso
   * aparte: `cerrado` no es `aprobado`.
   *
   * `esArchivable` **se conserva con su significado de siempre** —«lo que la
   * máquina dio por bueno»— porque lo usa `noArchivables()` y porque la
   * distinción entre las dos cosas sigue siendo el requisito (R39).
   */
  function esCirculable(parte) {
    return estadoDe(parte) === ESTADO_APROBADO;
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
   * F-026 R51 · los valores efectivos de los NUEVE campos, en un objeto plano.
   *
   * Es lo que el autoguardado compara para saber si hay algo que guardar: sin
   * una foto de lo que quedó guardado, la primera pulsación de cada parte
   * escribiría en la base aunque no hubiera cambiado nada.
   *
   * Vive aquí y no en `js/autoguardado.js` porque «cuál es el valor efectivo
   * de un campo» ya lo responde `valorDeCampo`, y dos formas de responder a la
   * misma pregunta son dos formas de divergir.
   */
  function valoresDeCampos(parte) {
    const valores = {};
    CAMPOS_DEL_PARTE.forEach(function (nombre) {
      valores[nombre] = valorDeCampo(parte || {}, nombre);
    });
    return valores;
  }

  /**
   * El `multipart` de `POST /api/archivar`: el fichero y **cinco** campos (R20).
   *
   * Se niega a componer nada que no **conste aprobado** (F-028 R33), o que ya
   * esté archivado. No basta con no pintar el botón: aunque se pulse dos veces,
   * aquí se para.
   *
   * Lo que se declara en el cuerpo es el **veredicto real**, el que emitió
   * F-004: la decisión de la persona se registra al lado, nunca encima (R8). El
   * backend lee el estado del almacén y nunca del cuerpo (R33).
   */
  function cuerpoDeArchivo(parte, FabricaFormData) {
    if (!esCirculable(parte)) {
      throw new Error(
        "este parte no consta aprobado, así que no se archiva: está " +
          `«${estadoDe(parte) || "sin estado conocido"}». Solo se archiva lo ` +
          "que la validación dio por bueno o lo que alguien aprobó a mano",
      );
    }
    // El veredicto que se declara en el cuerpo es el **real**, el que emitió
    // F-004, y hay que tenerlo. Antes de F-028 esta comprobación sobraba
    // —`esCirculable` miraba la validación—, pero ahora mira solo el estado, y
    // sin esto un parte sin veredicto reventaría con un `TypeError` en vez de
    // decir qué le falta.
    if (!parte.validacion || !parte.validacion.veredicto) {
      throw new Error(
        "este parte todavía no tiene veredicto, así que no se puede " +
          "archivar: lo que viaja en el cuerpo es el veredicto real que " +
          "emitió la validación, y aquí no hay ninguno",
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
   * F-009 · ¿se puede pedir el cierre de este parte?
   *
   * Las **dos precondiciones propias** del cierre, y ninguna más: el parte
   * entra en el circuito —su estado es `aprobado` (F-028 R33)— y **consta
   * archivado**. El backend las vuelve a comprobar —aquí no se decide
   * nada, se decide allí—, pero pararlo antes evita ofrecer un botón que va a
   * responder 409.
   *
   * Lo que **no** se comprueba, y es deliberado: si la incidencia tiene el
   * parte subido a Sigrid. El orden que decidió el humano es validar → cerrar
   * → subir el PDF, y ese último paso todavía no existe.
   */
  function esCerrable(parte) {
    return Boolean(
      parte &&
        parte.archivado &&
        esCirculable(parte) &&
        // El veredicto viaja en los dos cuerpos, así que tiene que existir.
        // Lo pedía `esCirculable` hasta F-028; ahora que ese solo mira el
        // estado, se pide aquí y no se da por supuesto.
        parte.validacion &&
        parte.validacion.veredicto &&
        valorDeCampo(parte, "numero_incidencia"),
    );
  }

  /**
   * F-009 · el cuerpo de `POST /api/cerrar`.
   *
   * **Por omisión es un dry-run**: `commit` y `confirmado` solo se ponen si
   * quien llama los pide, y el backend solo acepta el `true` de JSON. Quien
   * componga este cuerpo sin pensar no cierra nada en el ERP de producción.
   *
   * **No lleva los bytes del PDF ni ningún campo manuscrito** (R51): este
   * endpoint no sube nada, y el DNI y las observaciones del cliente no tienen
   * por qué viajar otra vez. Solo el `hash`, el número de incidencia, el
   * veredicto, el estado del archivo y quién lo pide.
   *
   * Se niega a componer nada que no cumpla las precondiciones: no basta con no
   * pintar el botón, porque aunque se pulse dos veces, aquí se para.
   */
  function cuerpoDeCierre(parte, opciones) {
    if (!esCerrable(parte)) {
      throw new Error(
        "este parte no se puede cerrar todavía: hace falta que conste " +
          `aprobado —está «${estadoDe(parte) || "sin estado conocido"}»—, ` +
          "que conste archivado y que tenga número de incidencia",
      );
    }

    const ajustes = opciones || {};
    if (!ajustes.usuarioOid) {
      throw new Error(
        "no se sabe quién pide el cierre: sin el identificador del usuario no " +
          "se puede firmar la incidencia en el ERP",
      );
    }

    const cuerpo = {
      hash: parte.hash,
      numero_incidencia: valorDeCampo(parte, "numero_incidencia"),
      veredicto: parte.validacion.veredicto,
      destino: parte.validacion.destino,
      estado_archivo: ESTADO_ARCHIVADO,
      usuario_oid: ajustes.usuarioOid,
    };
    if (ajustes.correo) {
      // Solo hace falta la primera vez de cada persona, para derivar el login
      // candidato que el ERP tendrá que confirmar. Quien ya tiene su
      // correspondencia guardada no lo necesita.
      cuerpo.correo = ajustes.correo;
    }
    if (ajustes.commit === true) {
      cuerpo.commit = true;
    }
    if (ajustes.confirmado === true) {
      cuerpo.confirmado = true;
    }
    return cuerpo;
  }

  /**
   * F-012 · ¿este parte ya consta adjuntado al ERP?
   *
   * Lo dice **el backend**, no el front: `parte.grafico` es el estado que
   * devolvió `/api/adjuntar`, y el backend lo saca de su traza. Aquí no se
   * deduce nada — deducirlo sería afirmar que un parte está dentro de Sigrid
   * mirando una variable de un navegador.
   *
   * Es lo que decide **si se pide el cierre** (R64): un gráfico que no llegó a
   * adjuntarse no puede ir seguido de un cierre, o volveríamos a producir la
   * anomalía que esta feature elimina.
   */
  function estaAdjuntado(parte) {
    return Boolean(parte && parte.grafico === ESTADO_ADJUNTADO);
  }

  /**
   * F-012 · el `multipart` de `POST /api/adjuntar`: el fichero y ocho campos.
   *
   * Se niega a componer nada que no sea cerrable —las mismas dos
   * precondiciones que el cierre, más el número de incidencia—: no basta con
   * no pintar el botón, porque aunque se pulse dos veces, aquí se para.
   *
   * **Por omisión es un dry-run**: `commit` y `confirmado` solo se ponen si
   * quien llama los pide, y viajan como la cadena `"true"` porque el backend
   * solo acepta exactamente eso.
   *
   * Lo que **sí** lleva y `cuerpoDeCierre` no: **los bytes del PDF**. Son los
   * mismos que se mandaron a `archivar` —el mismo objeto `File`—, que es lo
   * que hace que en Sigrid acabe el mismo documento que hay en SharePoint.
   *
   * Lo que **no** lleva: ningún campo manuscrito. El DNI y las observaciones
   * del cliente no viajan otra vez; van dentro del PDF, que es donde tienen
   * que estar.
   */
  function cuerpoDeGrafico(parte, opciones, FabricaFormData) {
    if (!esCerrable(parte)) {
      throw new Error(
        "este parte no se puede adjuntar todavía: hace falta que conste " +
          `aprobado —está «${estadoDe(parte) || "sin estado conocido"}»—, ` +
          "que conste archivado y que tenga número de incidencia",
      );
    }
    if (!parte.fichero) {
      throw new Error(
        "este parte no trae su PDF, así que no hay nada que adjuntar al ERP",
      );
    }

    const ajustes = opciones || {};
    if (!ajustes.usuarioOid) {
      throw new Error(
        "no se sabe quién pide el gráfico: sin el identificador del usuario " +
          "no se puede firmar el documento en el ERP",
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
    cuerpo.append(
      "numero_incidencia",
      valorDeCampo(parte, "numero_incidencia") || "",
    );
    cuerpo.append("veredicto", parte.validacion.veredicto);
    cuerpo.append("destino", parte.validacion.destino);
    cuerpo.append("estado_archivo", ESTADO_ARCHIVADO);
    cuerpo.append("usuario_oid", ajustes.usuarioOid);
    if (ajustes.correo) {
      // Solo hace falta la primera vez de cada persona, para derivar el login
      // candidato que el ERP tendrá que confirmar.
      cuerpo.append("correo", ajustes.correo);
    }
    if (ajustes.commit === true) {
      cuerpo.append("commit", "true");
    }
    if (ajustes.confirmado === true) {
      cuerpo.append("confirmado", "true");
    }
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
   * Procesa una remesa entera: **registra primero, procesa después** (R25).
   *
   * Esta función existe por un defecto concreto. En la primera versión de
   * F-019 el orden vivía en `app.js`, que no ejecuta ningún test, y la review
   * lo demostró borrando la línea que registraba la remesa: los 122 tests
   * siguieron en verde. Es el mismo defecto que F-019 viene a matar —«el
   * endpoint existe y nadie lo llama»— un nivel más arriba, así que el orden
   * se muda aquí, que es donde vive «qué se pide y en qué orden» y donde hay
   * tests que lo miran.
   *
   * El registro va antes porque `postventa.partes.remesa_id` tiene clave
   * ajena contra `postventa.remesas.id`: sin remesa registrada, cada guardado
   * responde 409 y ningún parte se puede archivar.
   *
   * **Un registro fallido no tumba la carga.** Leer y revisar los partes
   * sigue siendo útil aunque no se puedan archivar, y tumbarla castigaría al
   * usuario por una avería de la base. Lo que sí ocurre es que se devuelve un
   * `remesaId` vacío, y con él cada parte queda no archivable **con su
   * motivo** (R27), en vez de descubrirse al pulsar el botón.
   *
   * @param {Object} datos Lo que devolvió `POST /api/split`.
   * @param {Object} api El cliente de `js/api.js`.
   * @param {Object} [opciones] `nombreOrigen` y `procesar(remesaId)`, que es
   *        lo que la pantalla haga con cada parte —en `app.js`, pasarlos por
   *        la cola de concurrencia—.
   * @returns {Promise<{remesaId: string, avisos: string[]}>}
   */
  async function procesarRemesa(datos, api, opciones) {
    const ajustes = opciones || {};
    const partes = (datos && datos.partes) || [];
    // Copia: la respuesta de `/api/split` no se muta, que es lo que permite
    // volver sobre ella.
    const avisos = ((datos && datos.avisos) || []).slice();

    let remesaId = "";
    try {
      const registro = await api.registrarRemesa({
        nombre_origen: ajustes.nombreOrigen || "",
        num_partes: partes.length,
        avisos: avisos,
      });
      remesaId = (registro && registro.remesa_id) || "";
    } catch (error) {
      avisos.push(
        AVISO_SIN_REMESA + ((error && error.mensaje) || String(error)),
      );
    }

    if (ajustes.procesar) {
      await ajustes.procesar(remesaId);
    }
    return { remesaId: remesaId, avisos: avisos };
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
   * F-028 · el cuerpo de `POST /api/estado`: el de guardar **más cuatro claves**.
   *
   * Es el relevo de `cuerpoDeAprobacion`, y hace lo que aquel no podía: además
   * de aprobar un parte que la máquina rechazó, **rechazar uno que la máquina
   * dio por bueno**. Por eso aquí no se pregunta si el parte «es aprobable»:
   * una persona puede mover a `aprobado` o a `rechazado` cualquier parte que no
   * esté `cerrado` (R9, R10), y lo que impide que un parte sin código de obra
   * acabe archivado no es un veto de la pantalla, son las tres puertas del
   * backend y el veredicto de F-004.
   *
   * El backend hace **las dos cosas en una llamada** —guarda el parte con su
   * veredicto y escribe la decisión con la huella de *ese mismo* veredicto—,
   * así que necesita exactamente lo que necesita `/api/parte`: los nueve campos
   * y la lectura de la firma, **con las correcciones de la persona aplicadas**.
   * Recortar la extracción cambiaría el veredicto sobre el que se decide, y la
   * huella apuntada dejaría de ser la del veredicto que se está mirando.
   *
   * Lo que **no** lleva, igual que `cuerpoDeParte`: ni los bytes del PDF —el
   * documento vive en SharePoint— ni ningún veredicto ya hecho, que el backend
   * recalcula y no acepta del cuerpo (R28, R30).
   *
   * `confirmado` es el **booleano** de JSON. El backend rechaza a propósito la
   * cadena `"true"`, y con razón: es el error clásico de un cliente que
   * serializa mal, y tratarlo como confirmación dejaría un parte rechazado a
   * nombre de alguien que no lo rechazó — un parte que deja de archivarse y de
   * cerrar su incidencia sin que nadie se entere. No es una segunda
   * confirmación de pantalla (R29): el botón **es** el acto explícito.
   *
   * **Se niega a componer** —no basta con no pintar el botón, porque aunque se
   * pulse dos veces aquí se para— cuando falta algo de lo que hace que la
   * decisión signifique algo:
   *
   *   1. un destino que no sea uno de los dos manuales (R10);
   *   2. sin `usuarioOid`: una decisión anónima no es una decisión (R14);
   *   3. un **rechazo sin motivo** (R11). Es la única de las cuatro que no se
   *      puede recuperar después: quien vuelva a mirar el parte —otra persona,
   *      o la misma dentro de un mes— necesita saber qué había que arreglar, y
   *      «rechazado» a secas obliga a mirar el papel entero otra vez;
   *   4. sin remesa registrada, porque el backend respondería 409.
   *
   * El orden es **el del backend** (`estado`, `usuario_oid`, `confirmado`,
   * `motivo`, y la remesa después) para que el error que se enseñe aquí sea el
   * mismo que habría respondido la petición.
   *
   * @param {object} parte El parte de la pantalla, con su extracción y su firma.
   * @param {{estado: string, usuarioOid: string, remesaId: string,
   *          motivo?: string}} opciones
   */
  function cuerpoDeCambioDeEstado(parte, opciones) {
    const ajustes = opciones || {};
    if (ESTADOS_MANUALES.indexOf(ajustes.estado) === -1) {
      throw new Error(
        "a este parte solo se le puede pedir 'aprobado' o 'rechazado': a " +
          "'pendiente' no se vuelve a mano, y a 'cerrado' solo se llega " +
          "cerrando la incidencia en el ERP",
      );
    }
    // El `oid` se recorta antes de mirarlo, como hace el backend: una cadena
    // de espacios es `truthy` en JavaScript, así que sin recortar se compondría
    // una petición con `usuario_oid: "   "` que el backend contesta con un 400.
    const usuarioOid = normalizarValor(ajustes.usuarioOid);
    if (!usuarioOid) {
      throw new Error(
        "no se sabe quién decide sobre este parte: sin el identificador del " +
          "usuario no se puede registrar quién se hizo responsable",
      );
    }

    const motivo = normalizarValor(ajustes.motivo);
    if (!motivo && ajustes.estado === ESTADO_RECHAZADO) {
      throw new Error(
        "rechazar un parte sin decir por qué deja a quien vuelva a mirarlo " +
          "sin saber qué hay que arreglar: el motivo es obligatorio al rechazar",
      );
    }
    if (motivo && motivo.length > LIMITE_MOTIVO) {
      throw new Error(
        `el motivo no puede pasar de ${LIMITE_MOTIVO} caracteres: es para ` +
          "explicar la decisión, no para copiar ahí el parte",
      );
    }
    if (!ajustes.remesaId) {
      throw new Error(
        "no hay ninguna remesa registrada para este parte: vuelve a subir la " +
          "remesa para que quede constancia antes de decidir sobre él",
      );
    }

    const cuerpo = cuerpoDeParte(parte, ajustes.remesaId);
    cuerpo.estado = ajustes.estado;
    cuerpo.usuario_oid = usuarioOid;
    cuerpo.confirmado = true;
    if (motivo) {
      // Un motivo vacío **no viaja como clave vacía**: el backend distingue
      // «no hay motivo» de «el motivo está en blanco», y al aprobar es
      // opcional (R12).
      cuerpo.motivo = motivo;
    }
    return cuerpo;
  }

  /**
   * Guarda el parte y su veredicto. **Nunca lanza** (F-019 R27).
   *
   * Devuelve `{ok, motivo, estado}`. Un guardado fallido no es un error
   * del proceso:
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
      const datos = await api.guardarParte(
        cuerpoDeParte(parte, remesaId),
        parte.hash,
      );
      return {
        ok: true,
        motivo: "",
        // F-028 R38 · el estado de este parte según el backend, **después** de
        // guardar. Viene de aquí y no de una petición aparte —serían 22
        // llamadas de más en una remesa real—, y es lo que permite que al
        // volver a subir la remesa cada parte se reconozca con el estado que
        // tiene en la base: aprobado por alguien, rechazado, o ya cerrado.
        //
        // Hasta T14 esta clave era `aprobacion` y hablaba de la tabla de
        // F-026, que ya no se lee. Lo que llega ahora es el bloque `estado`.
        estado: (datos && datos.estado) || null,
      };
    } catch (error) {
      return {
        ok: false,
        motivo:
          (error && error.mensaje) ||
          (error && error.message) ||
          String(error),
        // Un guardado fallido no dice nada del estado: no se inventa ninguno,
        // y quien lo tuviera se queda con el que ya tenía. Ponerlo a `null`
        // borraría de la pantalla una decisión que sigue escrita en la base.
        estado: null,
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

  // =======================================================================
  // F-025 · El circuito de UN parte: archivar, adjuntar y cerrar del tirón
  // =======================================================================
  //
  // Todo esto vivía en `js/app.js` repartido entre `_archivarUno`,
  // `_adjuntarYCerrarUno` y `_cerrarUno`, que es **la única habitación de la
  // casa sin tests**. F-019 ya demostró una vez lo que eso cuesta: el orden
  // «registrar la remesa antes de procesar» vivía allí, se borró la línea y
  // los 122 tests siguieron en verde. Lo que F-025 dejaría allí sería el orden
  // de **tres escrituras, dos de ellas en un ERP de producción**, así que se
  // muda aquí, que es donde vive «qué se pide y en qué orden» y donde hay
  // tests que lo miran.

  /**
   * F-025 R24 · los partes que la tanda tiene que llevar hasta cerrado.
   *
   * **Un solo selector**, y por eso es más ancho que el `archivables()` que
   * sustituye: apto, guardado y **no cerrado**. Los dos casos que el viejo
   * dejaba fuera son justo los que hay que recuperar —archivado sin adjuntar,
   * y adjuntado sin cerrar—, y al fundirse los dos botones en uno se quedarían
   * sin ninguna forma de volver a entrar.
   *
   * Lo que **no** entra: los partes que la validación mandó a revisión o a la
   * cola humana **y que no consta que haya aprobado nadie** (R36 de F-025, y
   * R25 de F-026). Desde F-026 el selector pregunta por `esCirculable` —apto
   * **o** aprobado vigente—, y esa es la única puerta que la aprobación abre:
   * el parte sigue teniendo que constar guardado y no estar cerrado.
   */
  function pendientesDeCircuito(partes) {
    return (partes || []).filter(function (parte) {
      return Boolean(
        parte && !parte.cerrado && parte.guardado && esCirculable(parte),
      );
    });
  }

  /**
   * F-025 R12 · el porcentaje sobre el tamaño de **la tanda**, no de la remesa.
   *
   * El denominador viejo era el total de la remesa, así que archivar 4 partes
   * de 22 enseñaba un 18 % al terminar: una barra que nunca llega al final
   * parece un proceso colgado, y detrás de este hay escrituras en un ERP.
   */
  function porcentajeDeTanda(hechos, total) {
    return total ? Math.round((hechos / total) * 100) : 0;
  }

  /** El texto de un fallo, venga de `js/api.js` o de un reventón cualquiera. */
  function mensajeDeError(error) {
    return (
      (error && error.mensaje) || (error && error.message) || String(error)
    );
  }

  /** El número de incidencia que devolvió el backend, si lo devolvió (R37). */
  function numeroDeIncidenciaDe(datos, actual) {
    const numero = datos && datos.numero_incidencia;
    return numero ? String(numero) : actual;
  }

  /**
   * Anota un fallo en el resultado y lo devuelve. **No lanza** (R20).
   *
   * `ambito` solo se rellena cuando el fallo es **de entorno**, porque es lo
   * único que dice: qué ventana de escritura está cerrada. Son dos distintas
   * —`ARCHIVO_HABILITADO` y `CIERRE_HABILITADO`— y la tanda las trata al revés
   * (R21, R22): con el ERP cerrado se sigue archivando; sin archivo no hay
   * nada que adjuntar ni que cerrar.
   */
  function anotarFallo(resultado, estado, ambito, error) {
    const deEntorno = Boolean(error && error.tipo === "entorno");
    resultado.estado = estado;
    resultado.error = mensajeDeError(error);
    resultado.tipoError = deEntorno ? "entorno" : "parte";
    resultado.ambito = deEntorno ? ambito : "";
    return resultado;
  }

  /**
   * F-025 · el circuito de UN parte: archivar → adjuntar → cerrar.
   *
   * **Nunca lanza** (R20): devuelve hasta dónde llegó, porque un parte roto no
   * puede tumbar la tanda. Castigar a diecinueve partes buenos por uno cuyo
   * número de incidencia se leyó mal sería exactamente lo que R10 de F-007
   * prohíbe.
   *
   * **Los dos pasos del ERP van siempre con `commit` y `confirmado`** (R8), y
   * eso es seguro porque la llamada con `commit` **lleva dentro su propia
   * comprobación previa** contra el ERP y contra la pasarela: está recorrido
   * en `design.md` §2 y vigilado por
   * `services/postventa-api/tests/test_f025_sin_dry_run_previo.py`. Lo que
   * desaparece con F-025 es la pantalla, no la verificación.
   *
   * **No muta el parte.** Lo que hay que mover al estado de Alpine lo dice el
   * resultado (`archivado`, `grafico`, `cerrado`), y de eso se encarga
   * `app.js`: aquí se decide, allí se pinta.
   *
   * Cada paso **se salta si ya consta hecho** (R25, R26). Saltarlo aquí ahorra
   * una petición; la defensa de verdad está en el backend —la traza de F-006,
   * la traza del gráfico y la pasarela por `sha256`— y sigue donde estaba.
   *
   * @param {Object} parte El parte de la pantalla.
   * @param {Object} api El cliente de `js/api.js`.
   * @param {Object} [opciones] `{usuarioOid, correo, alPaso(paso), erpCerrado,
   *        FabricaFormData}`. `erpCerrado` es la bandera de R21: entra y sale
   *        por parámetro para que la decisión sea pura y tenga test, en vez de
   *        un `if` dentro de un `catch` de Alpine.
   * @returns {Promise<{paso: string, estado: string, archivado: boolean,
   *          grafico: string, cerrado: boolean, numeroIncidencia: string,
   *          mensaje: string, error: string, tipoError: string,
   *          ambito: string, archivo: Object|null}>}
   */
  async function ejecutarCircuito(parte, api, opciones) {
    const ajustes = opciones || {};
    const anunciar =
      typeof ajustes.alPaso === "function" ? ajustes.alPaso : function () {};
    // Las credenciales y el `commit` van juntos en un solo objeto: que no haya
    // ninguna forma de componer el cuerpo del ERP **sin** `commit` es R8.
    const credenciales = {
      usuarioOid: ajustes.usuarioOid,
      correo: ajustes.correo,
      commit: true,
      confirmado: true,
    };
    const resultado = {
      paso: "",
      estado: "",
      archivado: Boolean(parte && parte.archivado),
      grafico: (parte && parte.grafico) || "",
      cerrado: false,
      numeroIncidencia: "",
      mensaje: "",
      error: "",
      tipoError: "",
      ambito: "",
      archivo: null,
    };

    // --- paso 1 · el documento a SharePoint -------------------------------
    if (!resultado.archivado) {
      resultado.paso = "archivar";
      anunciar(PASO_ARCHIVANDO);
      try {
        // `cuerpoDeArchivo` se niega a componer nada que no sea apto, que no
        // esté guardado o que ya esté archivado (R36): aunque se pulse dos
        // veces, aquí se para. Su negativa sale como resultado y no como
        // excepción, para no tumbar la tanda.
        resultado.archivo = await api.archivar(
          cuerpoDeArchivo(parte, ajustes.FabricaFormData),
          parte.hash,
        );
        resultado.archivado = true;
      } catch (error) {
        return anotarFallo(resultado, "error_archivo", "archivo", error);
      }
    }
    resultado.estado = ESTADO_ARCHIVADO;

    // R21 · la ventana del ERP ya se sabe cerrada por un parte anterior de
    // esta misma tanda. No se vuelve a preguntar: no se va a abrir a mitad de
    // tanda, y veinte partes por dos llamadas de 503 garantizado es ruido.
    // Pero el archivo SÍ sirve, y por eso este corte va **después** del paso 1.
    if (ajustes.erpCerrado) {
      resultado.mensaje = MENSAJE_ERP_CERRADO;
      return resultado;
    }

    // El parte tal y como lo ven los dos pasos del ERP: con su archivo hecho.
    // `cuerpoDeGrafico` y `cuerpoDeCierre` exigen `archivado` (es R15 de F-012
    // y R17 de F-009, y el backend las vuelve a comprobar), y aquí acabamos de
    // archivarlo. Se compone una copia en vez de mutar la entrada.
    const conArchivo = resultado.archivado
      ? Object.assign({}, parte, { archivado: true })
      : parte;

    // --- paso 2 · el parte a su reclamación, con commit -------------------
    if (resultado.grafico !== ESTADO_ADJUNTADO) {
      resultado.paso = "adjuntar";
      anunciar(PASO_ADJUNTANDO);
      try {
        const datos = await api.adjuntar(
          cuerpoDeGrafico(conArchivo, credenciales, ajustes.FabricaFormData),
          parte.hash,
        );
        resultado.grafico = (datos && datos.estado) || "";
        resultado.numeroIncidencia = numeroDeIncidenciaDe(
          datos,
          resultado.numeroIncidencia,
        );
      } catch (error) {
        return anotarFallo(resultado, "error_grafico", "erp", error);
      }
    }

    if (resultado.grafico !== ESTADO_ADJUNTADO) {
      // R27 · lo normal aquí es `ya_cerrada`: la reclamación estaba cerrada
      // antes de que llegáramos y no se le cuelga un gráfico. **No es un
      // error** —es el reintento legítimo de una tanda— y el parte sale de la
      // lista para que no vuelva a entrar.
      resultado.estado = resultado.grafico;
      resultado.cerrado = true;
      resultado.mensaje =
        "no se ha adjuntado el parte (" +
        resultado.grafico +
        "): no se cierra nada";
      return resultado;
    }
    resultado.estado = ESTADO_ADJUNTADO;

    // --- paso 3 · el cierre, con commit -----------------------------------
    resultado.paso = "cerrar";
    anunciar(PASO_CERRANDO);
    try {
      const datos = await api.cerrar(
        cuerpoDeCierre(conArchivo, credenciales),
        parte.hash,
      );
      resultado.numeroIncidencia = numeroDeIncidenciaDe(
        datos,
        resultado.numeroIncidencia,
      );
      resultado.estado = (datos && datos.estado) || "cerrado";
      resultado.cerrado = true;
      resultado.mensaje =
        resultado.numeroIncidencia + " → " + resultado.estado;
    } catch (error) {
      // R19 · el gráfico YA está dentro de Sigrid y la incidencia sigue
      // abierta. El estado es `adjuntado`, no `error_cierre`: tiene salida
      // propia en pantalla —el recuadro ámbar con «Reintentar el cierre»
      // (R65 de F-012)— y decir «error» escondería que el parte ya está en el
      // ERP.
      return anotarFallo(resultado, ESTADO_ADJUNTADO, "erp", error);
    }

    return resultado;
  }

  // F-025 R14 · la guarda de reentrada de la tanda.
  //
  // Hay tres capas contra la doble pulsación y ninguna sobra: la confirmación
  // se consume al primer clic (`js/confirmacion.js`), esta guarda, y los pasos
  // saltables de `ejecutarCircuito`. Hasta ahora la única defensa era el
  // `:disabled` del HTML, que **ningún test ejecuta**.
  //
  // Vive aquí, y no en `app.js`, exactamente por eso.
  let tandaEnCurso = false;

  /** ¿Hay una tanda corriendo ahora mismo? */
  function hayTandaEnCurso() {
    return tandaEnCurso;
  }

  /**
   * Ejecuta `ejecutar` solo si no hay otra tanda en curso (R14).
   *
   * @returns {Promise<{arrancada: boolean, valor: *}>} `arrancada: false`
   *          cuando ya había una corriendo, y entonces no se ha llamado a
   *          nada.
   *
   * La guarda se suelta en un `finally`: una tanda que reviente por lo que sea
   * no puede dejar la pantalla bloqueada hasta que alguien recargue.
   */
  async function conGuardaDeTanda(ejecutar) {
    if (tandaEnCurso) {
      return { arrancada: false, valor: undefined };
    }
    tandaEnCurso = true;
    try {
      return { arrancada: true, valor: await ejecutar() };
    } finally {
      tandaEnCurso = false;
    }
  }

  const Pipeline = {
    CAMPOS_DEL_PARTE: CAMPOS_DEL_PARTE,
    CAMPOS_DE_ARCHIVO: CAMPOS_DE_ARCHIVO,
    UMBRAL_CONFIANZA: UMBRAL_CONFIANZA,
    AVISO_SIN_REMESA: AVISO_SIN_REMESA,
    procesarRemesa: procesarRemesa,
    normalizarValor: normalizarValor,
    aplicarEdiciones: aplicarEdiciones,
    cuerpoDeValidacion: cuerpoDeValidacion,
    camposDudosos: camposDudosos,
    semaforoDe: semaforoDe,
    esArchivable: esArchivable,
    esCerrable: esCerrable,
    valorDeCampo: valorDeCampo,
    valoresDeCampos: valoresDeCampos,
    cuerpoDeArchivo: cuerpoDeArchivo,
    // F-026, conservado · quién entra en el circuito. La aprobación humana en
    // sí se fue con F-028 T18: ver el recuadro del principio del fichero.
    SEMAFORO_APROBADO: SEMAFORO_APROBADO,
    esCirculable: esCirculable,
    // F-028 · el estado del parte: qué se puede pedir, qué viaja al pedirlo y
    // qué marca se pinta con lo que contesta el backend.
    //
    // Los cuatro literales de estado se exportan para que `js/app.js` compare
    // contra ellos en vez de escribirlos otra vez: dos literales para el mismo
    // estado divergen en la primera corrección, y el que manda es el del
    // backend.
    ESTADO_APROBADO: ESTADO_APROBADO,
    ESTADO_RECHAZADO: ESTADO_RECHAZADO,
    ESTADO_PENDIENTE: ESTADO_PENDIENTE,
    ESTADO_CERRADO: ESTADO_CERRADO,
    ESTADOS_MANUALES: ESTADOS_MANUALES,
    LIMITE_MOTIVO: LIMITE_MOTIVO,
    SEMAFORO_RECHAZADO: SEMAFORO_RECHAZADO,
    SEMAFORO_CERRADO: SEMAFORO_CERRADO,
    AVISO_DECISION_CADUCADA: AVISO_DECISION_CADUCADA,
    cuerpoDeCambioDeEstado: cuerpoDeCambioDeEstado,
    estadoDe: estadoDe,
    avisoDeEstado: avisoDeEstado,
    cuerpoDeCierre: cuerpoDeCierre,
    cuerpoDeGrafico: cuerpoDeGrafico,
    estaAdjuntado: estaAdjuntado,
    cuerpoDeParte: cuerpoDeParte,
    ficheroDeParte: ficheroDeParte,
    procesarParte: procesarParte,
    guardarParte: guardarParte,
    revalidar: revalidar,
    revalidarYGuardar: revalidarYGuardar,
    // F-025 · el circuito de la confirmación única.
    ESTADO_ADJUNTADO: ESTADO_ADJUNTADO,
    MENSAJE_ERP_CERRADO: MENSAJE_ERP_CERRADO,
    pendientesDeCircuito: pendientesDeCircuito,
    porcentajeDeTanda: porcentajeDeTanda,
    ejecutarCircuito: ejecutarCircuito,
    conGuardaDeTanda: conGuardaDeTanda,
    hayTandaEnCurso: hayTandaEnCurso,
  };

  if (typeof window !== "undefined") {
    window.Pipeline = Pipeline;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = Pipeline;
  }
})();
