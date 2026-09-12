// services/postventa-front/js/app.js
// El estado de Alpine y NADA MÁS. Regla de oro del diseño (`design.md` §3):
// **si algo merece un test, no vive aquí**. Este fichero mueve estado de la
// pantalla y llama a los módulos, que son los que se prueban:
//
//   js/seleccion.js  qué entra en la remesa y cómo se envía  (R1-R4)
//   js/cola.js       el límite de concurrencia               (R7-R12)
//   js/api.js        timeout, reintentos, clasificación      (R23-R27)
//   js/pipeline.js   qué se pide, en qué orden y qué viaja   (R8, R13-R22)
//                    y, desde F-025, el CIRCUITO de un parte:
//                    archivar → adjuntar → cerrar            (F-025 R7)
//   js/confirmacion.js  el doble clic antes de escribir. Desde
//                       F-025 es UNA sola confirmación para
//                       los tres pasos           (R19, F-009 R15, F-025 R2)
//   js/traza.js      el único registro permitido             (R28)
//
// Aquí no hay ni un bucle de reintento, ni un cálculo de veredicto, ni una
// composición de cuerpo de petición. Si aparece alguno, está en el sitio
// equivocado.

function appPostventa() {
  const config = window.CONFIG_POSTVENTA;
  const api = window.Api.crearApi({ baseApi: config.baseApi, config: config });

  // F-026 R51 · el autoguardado de las correcciones. Vive en el cierre y no en
  // el estado de Alpine a propósito: no es un dato que se pinte —lo que se
  // pinta son `estadoAutoguardado` y `mensajeAutoguardado`, que sí están
  // declarados abajo— y meterlo en el estado lo envolvería en el proxy
  // reactivo sin ninguna ganancia. Se monta en `_autoguardado()`.
  let autoguardado = null;

  return {
    // --- estado del servicio (R27) ---
    estadoServicio: "comprobando",
    mensajeServicio: "Comprobando el servicio…",
    version: "",

    // --- fase de la pantalla (`design.md` §4) ---
    fase: "inactivo",
    arrastrando: false,
    errorGlobal: "",

    // --- selección (R1-R3) ---
    seleccion: [],
    mensajeDescartes: "",
    errorSeleccion: "",

    // --- remesa y partes (R5-R6) ---
    avisosRemesa: [],
    partes: [],
    terminados: 0,

    // --- persistencia (F-019 R25) ---
    // El `remesa_id` que devolvió `POST /api/remesa`. Se conserva mientras
    // dure la remesa en pantalla y se reenvía en cada guardado: la tabla de
    // remesas no tiene clave natural (decisión D2), así que perderlo y
    // resubir crearía una fila de remesa de más.
    remesaId: "",

    // --- parte abierto (R14-R18) ---
    parteAbierto: null,
    urlPdf: "",
    mensajeRevalidacion: "",
    // F-026 R52 · los tres estados del autoguardado —guardando, guardado y no
    // se ha podido guardar— y su texto. **Nacen declarados** para que Alpine
    // los haga reactivos: añadirlos a mitad de sesión no repintaría nada, que
    // es el defecto que F-025 documentó con `paso`. Y lo que se pinta cuando
    // el guardado falla es lo único que separa «no se guardó» de que la
    // persona suponga que sí.
    estadoAutoguardado: "",
    mensajeAutoguardado: "",
    // F-026 · qué pasó con la última aprobación que se pidió. Nace declarado
    // para que Alpine lo haga reactivo, como todo lo demás de esta pantalla.
    mensajeAprobacion: "",
    CAMPOS: window.Pipeline.CAMPOS_DEL_PARTE,

    // --- archivar y cerrar, en un solo gesto (F-025 R1, R2) ---
    // El estado de la confirmación lo compone `js/confirmacion.js`: aquí solo
    // se guarda lo que devuelve, sin interpretarlo. Desde F-025 es **la
    // única** confirmación del circuito, y cubre los tres pasos: el archivo en
    // SharePoint, el gráfico adjunto a la reclamación y el cierre.
    confirmacionArchivo: null,
    avisoArchivo: "",
    entornoNoArchiva: "",
    resultadosArchivo: [],

    // F-025 R12 · el denominador de la barra es el tamaño de **la tanda**, no
    // el de la remesa. Con el viejo, archivar 4 partes de 22 enseñaba un 18 %
    // al terminar, y una barra que no llega al final parece un proceso
    // colgado.
    totalTanda: 0,

    // F-025 R21 · la ventana de escritura del ERP se ha encontrado cerrada.
    // Los partes que queden **siguen archivando** y no le piden nada al ERP:
    // veinte partes por dos llamadas de 503 garantizado es ruido, y el archivo
    // sí sirve —deja el documento guardado y el parte listo para la tanda
    // siguiente—.
    erpCerrado: false,

    // F-025 R22 · la ventana del **archivo** se ha encontrado cerrada, y eso
    // sí para la tanda: sin archivo no hay nada que adjuntar ni que cerrar.
    tandaDetenida: false,

    // --- cierre en Sigrid (F-009) ---
    // Quién dice ser el usuario, para poder firmar el cierre en el ERP. Lo
    // sirve el proxy de la Static Web App y NO está firmado: es una traza de
    // quién lo pidió, no un control de acceso. Con quién se firma de verdad lo
    // decide el ERP, que tiene que confirmar el login antes de escribir nada.
    usuario: { usuarioOid: "", correo: "" },
    // F-025 R5 · aquí vivían `dryRunCierre` y `dryRunGrafico`, el cálculo
    // previo que se enseñaba **antes** de confirmar. La pantalla previa se
    // retiró entera (P1, opción a): lo que desaparece es la pantalla, no la
    // verificación — el backend sigue haciendo su comprobación contra el ERP
    // dentro de la misma llamada que escribe (`design.md` §2).
    entornoNoCierra: "",
    resultadosCierre: [],

    // =====================================================================
    // Estado del servicio
    // =====================================================================
    async comprobarBackend() {
      try {
        const datos = await api.salud();
        this.estadoServicio = "ok";
        this.version = `${datos.servicio} ${datos.version}`;
        this.mensajeServicio = `Servicio disponible (entorno ${datos.entorno}).`;
      } catch (error) {
        this.estadoServicio = "error";
        this.mensajeServicio = error.mensaje || "No se puede contactar con el servicio.";
      }
    },

    // =====================================================================
    // Selección de ficheros (R1-R3)
    // =====================================================================
    alSoltar(evento) {
      this.arrastrando = false;
      this._aceptar(Array.from(evento.dataTransfer.files));
    },

    alElegirFicheros(evento) {
      this._aceptar(Array.from(evento.target.files));
      evento.target.value = ""; // permite volver a elegir lo mismo
    },

    _aceptar(ficheros) {
      const resultado = window.Seleccion.filtrarAdmitidos(ficheros);
      this.mensajeDescartes = resultado.mensajeDescartes;
      this.errorSeleccion = window.Seleccion.motivoDeRechazo(resultado);
      this.seleccion = resultado.admitidos;
      this.fase = this.seleccion.length ? "seleccionado" : "inactivo";
    },

    tamanoDe(fichero) {
      return window.Seleccion.formatearTamano(fichero.size);
    },

    // =====================================================================
    // Carga de la remesa (R4-R6)
    // =====================================================================
    async confirmarCarga() {
      if (!this.seleccion.length) {
        return;
      }
      this.fase = "troceando";
      this.errorGlobal = "";
      this.avisosRemesa = [];
      this.remesaId = "";

      try {
        const datos = await api.trocear(
          window.Seleccion.formDataDeRemesa(this.seleccion),
        );
        this.avisosRemesa = datos.avisos || [];
        this.partes = (datos.partes || []).map(this._parteInicial);
        this.terminados = 0;
        // F-019 R25: registrar la remesa ANTES de procesar ningún parte. El
        // orden lo decide `js/pipeline.js`, que es quien tiene tests: aquí
        // vivía antes, y borrar la línea dejaba la suite entera en verde.
        const remesa = await window.Pipeline.procesarRemesa(datos, api, {
          nombreOrigen: this._nombreDeLaRemesa(),
          procesar: (remesaId) => {
            this.remesaId = remesaId;
            return this._procesarRemesa();
          },
        });
        this.remesaId = remesa.remesaId;
        this.avisosRemesa = remesa.avisos;
      } catch (error) {
        // R6: se vuelve al estado inicial sin dejar filas a medias.
        this.partes = [];
        this.avisosRemesa = (error && error.avisos) || [];
        this.errorGlobal = (error && error.mensaje) || String(error);
        this.fase = "inactivo";
      }
    },

    _nombreDeLaRemesa() {
      // De qué fichero salió, para el histórico de remesas. Con varios, la
      // cuenta: el nombre es una traza, no una clave.
      if (this.seleccion.length === 1) {
        return this.seleccion[0].name;
      }
      return `${this.seleccion.length} ficheros`;
    },

    _parteInicial(crudo) {
      return {
        hash: crudo.hash,
        origen: crudo.origen,
        paginas_origen: crudo.paginas_origen,
        modo_deteccion: crudo.modo_deteccion,
        avisos: crudo.avisos || [],
        contenido_b64: crudo.contenido_b64,
        fichero: window.Pipeline.ficheroDeParte(crudo),
        estado: "pendiente",
        semaforo: "",
        error: "",
        // F-025 R13 · en cuál de los tres pasos está ahora mismo: archivando,
        // adjuntando o cerrando. Nace declarado para que Alpine lo haga
        // reactivo; añadirlo a mitad de tanda no repintaría la fila.
        paso: "",
        grafico: "",
        cerrado: false,
        extraccion: null,
        firma: null,
        validacion: null,
        ediciones: {},
        archivado: false,
        // F-019 R27: hasta que conste guardado, el parte no es archivable.
        guardado: false,
        errorGuardado: "",
        // F-026 R22 · lo que el backend dice de la aprobación de este parte:
        // `{estado, destino_aprobado, motivos_aprobados, aprobado_at_utc}`, o
        // `null` si no lo ha aprobado nadie. **Nace declarada** aunque nazca
        // vacía: añadirla a mitad de sesión no la haría reactiva y la marca
        // del parte aprobado no repintaría, que es el defecto que F-025
        // documentó con `paso`.
        //
        // Viene SIEMPRE del backend —de `/api/parte` o de `/api/aprobar`—,
        // nunca se compone aquí: quien decide si sigue vigente es quien la
        // escribió.
        aprobacion: null,
      };
    },

    // =====================================================================
    // Proceso parte a parte, por la cola (R7-R12)
    // =====================================================================
    async _procesarRemesa() {
      this.fase = "procesando";
      // F-025 R12 · el denominador de la barra es **el tamaño de la tanda**, y
      // esta tanda es la remesa entera. Un solo `totalTanda` para las dos
      // fases: dos denominadores serían dos formas de equivocarse.
      this.totalTanda = this.partes.length;
      await this._porLaCola(this.partes, (parte) => this._procesarUno(parte));
      this.fase = "revision";
    },

    _porLaCola(partes, tarea) {
      // La MISMA cola para procesar y para archivar: otra fase, mismo límite.
      return window.Cola.ejecutarConLimite(
        partes.map((parte) => () => tarea(parte)),
        config.CONCURRENCIA_PARTES,
        () => {
          this.terminados += 1;
        },
      );
    },

    async _procesarUno(parte) {
      parte.estado = "leyendo";
      parte.error = "";
      try {
        const resultado = await window.Pipeline.procesarParte(
          parte,
          api,
          this.remesaId,
        );
        parte.extraccion = resultado.extraccion;
        parte.firma = resultado.firma;
        this._anotarGuardado(parte, resultado.guardado);
        this._anotarVeredicto(parte, resultado.validacion);
      } catch (error) {
        parte.estado = "error";
        parte.semaforo = "";
        parte.error = (error && error.mensaje) || String(error);
      }
    },

    _anotarGuardado(parte, guardado) {
      // R27: un parte que no se pudo guardar NO es archivable, y el motivo se
      // enseña. Archivarlo fallaría igualmente con un 409, y hacerlo sin
      // decirlo devuelve al usuario al defecto 15: fichero arriba y sin
      // constancia, o un error que nadie sabe leer.
      parte.guardado = Boolean(guardado && guardado.ok);
      parte.errorGuardado = (guardado && guardado.motivo) || "";
      // F-026 R22, R31 · lo que el backend dice de la aprobación, después de
      // guardar. Solo se pisa cuando el guardado salió bien: un guardado
      // fallido no sabe nada de la aprobación, y ponerla a `null` borraría de
      // la pantalla una decisión que sigue escrita en la base.
      //
      // Cuando sí salió bien, esto es lo que hace que una revalidación que
      // **revocó** la aprobación se vea en el acto: la revocación ocurre en la
      // escritura, y esta es la respuesta de esa misma escritura.
      if (guardado && guardado.ok) {
        parte.aprobacion = guardado.aprobacion;
        // F-026 R51 · y lo que acaba de quedar guardado es contra lo que se
        // compara la siguiente pulsación. Sin esta foto, escribir el mismo
        // valor que ya está en la base dispararía un guardado de más.
        this._autoguardado().anotarGuardado(
          parte,
          window.Pipeline.valoresDeCampos(parte),
        );
      }
    },

    _anotarVeredicto(parte, validacion) {
      parte.validacion = validacion;
      // F-026 R36 · el semáforo mira las dos cosas: lo que dijo la máquina y
      // lo que decidió una persona. Un parte aprobado no se pinta como uno que
      // siempre fue verde.
      parte.semaforo = window.Pipeline.semaforoDe(validacion, parte.aprobacion);
      parte.estado = "listo";
    },

    async reintentarParte(parte) {
      // R11: el reintento pasa por la misma cola y respeta el mismo límite.
      this.terminados = Math.max(0, this.terminados - 1);
      await this._porLaCola([parte], (uno) => this._procesarUno(uno));
    },

    porcentaje() {
      // F-025 R12 · el cálculo vive en `js/pipeline.js`, que sí tiene tests, y
      // el denominador es `totalTanda`: el de la tanda en curso, no el de la
      // remesa entera.
      return window.Pipeline.porcentajeDeTanda(this.terminados, this.totalTanda);
    },

    tituloDeFase() {
      if (this.fase === "troceando") return "Troceando la remesa";
      if (this.fase === "archivando_y_cerrando") return "Archivando y cerrando";
      return "Procesando los partes";
    },

    // =====================================================================
    // Detalle, edición y revalidación (R14-R18)
    // =====================================================================
    abrirParte(parte) {
      this._revocarPdf();
      this.parteAbierto = parte;
      this.mensajeRevalidacion = "";
      // El mensaje de la aprobación anterior no es de este parte: dejarlo
      // diría «aprobado» encima de uno que nadie ha aprobado.
      this.mensajeAprobacion = "";
      // El PDF va desde un blob en memoria, nunca desde una URL con el
      // contenido dentro.
      this.urlPdf = URL.createObjectURL(parte.fichero);
    },

    cerrarParte() {
      this._revocarPdf();
      this.parteAbierto = null;
    },

    _revocarPdf() {
      // 22 blobs vivos es memoria que no vuelve.
      if (this.urlPdf) {
        URL.revokeObjectURL(this.urlPdf);
        this.urlPdf = "";
      }
    },

    valorDe(nombre) {
      const valor = window.Pipeline.valorDeCampo(this.parteAbierto, nombre);
      return valor === null ? "" : valor;
    },

    confianzaDe(nombre) {
      if (this.estaEditado(nombre)) {
        return 100; // D3: lo ha escrito una persona
      }
      const campos = (this.parteAbierto.extraccion || {}).campos || {};
      return campos[nombre] ? campos[nombre].confianza_pct : 0;
    },

    estaEditado(nombre) {
      return Object.prototype.hasOwnProperty.call(
        this.parteAbierto.ediciones,
        nombre,
      );
    },

    esDudoso(nombre) {
      return this.confianzaDe(nombre) < config.UMBRAL_CONFIANZA;
    },

    editarCampo(nombre, valor) {
      this.parteAbierto.ediciones[nombre] = valor;
      this.mensajeRevalidacion = "Hay correcciones sin revalidar.";
      // F-026 R50, R55 · y se guarda solo, tras la pausa, sin botón y sea cual
      // sea el veredicto del parte. Cuánto se espera y si hay algo que guardar
      // lo decide `js/autoguardado.js`, que sí tiene tests.
      this._autoguardado().alEscribir(this.parteAbierto, nombre, valor);
    },

    hayEdiciones() {
      return (
        this.parteAbierto && Object.keys(this.parteAbierto.ediciones).length > 0
      );
    },

    // =====================================================================
    // F-026 R50-R55 · el autoguardado de las correcciones
    // =====================================================================
    //
    // Aquí no se decide nada, como siempre: cuándo se guarda y si hay algo que
    // guardar está en `js/autoguardado.js`, y QUÉ se pide está en
    // `js/pipeline.js`. Esto ata las dos cosas al estado de Alpine.

    _autoguardado() {
      // Se monta la primera vez que alguien escribe, y no al crear el objeto,
      // porque las dos funciones que necesita —guardar y pintar— son métodos
      // de este objeto: montarlo antes obligaría a atarlas a mano.
      if (autoguardado === null) {
        autoguardado = window.Autoguardado.crearAutoguardado({
          // R51 · el retardo es el de la configuración. Ni uno inventado aquí,
          // ni uno por pantalla.
          retardoMs: config.RETARDO_AUTOGUARDADO_MS,
          guardar: (parte) => this._guardarCorreccion(parte),
          alCambiarEstado: (cambio) => this._pintarAutoguardado(cambio),
        });
      }
      return autoguardado;
    },

    async _guardarCorreccion(parte) {
      // R50 · **revalidar y guardar juntos**, con la misma función que usa el
      // botón. Guardar el campo sin revalidar dejaría en la base el veredicto
      // que la IA emitió sobre el dato SIN corregir, y las tres puertas de
      // F-026 leen ese veredicto.
      const resultado = await window.Pipeline.revalidarYGuardar(
        parte,
        api,
        this.remesaId,
      );
      this._anotarGuardado(parte, resultado.guardado);
      this._anotarVeredicto(parte, resultado.validacion);

      if (!parte.guardado) {
        // `guardarParte` no lanza cuando el backend rechaza: devuelve
        // `{ok: false, motivo}` para no tirar un veredicto ya pagado. Aquí eso
        // es un fallo de guardado y tiene que llegar a la pantalla (R52): sin
        // esto, la respuesta sería «Guardado» con la base sin tocar.
        throw new Error(parte.errorGuardado || "no se ha podido guardar");
      }
      return resultado;
    },

    _pintarAutoguardado(cambio) {
      // R52 · los tres estados. El de fallo se queda puesto hasta que un
      // guardado salga bien: no hay temporizador que lo borre.
      this.estadoAutoguardado = cambio.estado;
      this.mensajeAutoguardado = cambio.mensaje;
    },

    async revalidarParte() {
      const parte = this.parteAbierto;
      this.mensajeRevalidacion = "Revalidando…";
      try {
        // R17: SOLO /api/validar. No gasta IA.
        // F-019 R28: y se vuelve a guardar, para que lo guardado sea lo
        // revisado y no lo que dijo la IA la primera vez.
        const resultado = await window.Pipeline.revalidarYGuardar(
          parte,
          api,
          this.remesaId,
        );
        this._anotarGuardado(parte, resultado.guardado);
        this._anotarVeredicto(parte, resultado.validacion);
        this.mensajeRevalidacion = parte.guardado
          ? "Veredicto actualizado y guardado."
          : `Veredicto actualizado, pero NO se ha guardado: ${parte.errorGuardado}`;
      } catch (error) {
        this.mensajeRevalidacion = (error && error.mensaje) || String(error);
      }
    },

    // =====================================================================
    // Aprobación humana del parte (F-026)
    // =====================================================================
    //
    // Aquí no se decide nada, como siempre: qué es aprobable y qué viaja en la
    // petición está en `js/pipeline.js`, que sí tiene tests, y lo vuelve a
    // decidir el backend con el veredicto que él mismo recalcula (R5). Esto
    // mueve estado de Alpine y pide la petición.

    esAprobable(parte) {
      // R35, R39 · el gesto solo se ofrece cuando hay algo que decidir. Si al
      // parte le falta el código de obra o el número de incidencia, no hay
      // nada que aprobar: hay algo que teclear.
      const elegido = parte || this.parteAbierto;
      return window.Pipeline.esAprobable(elegido && elegido.validacion);
    },

    estaAprobado(parte) {
      // R36 · el cuarto estado del semáforo. Lo calcula `js/pipeline.js` al
      // anotar el veredicto; aquí solo se lee, para no tener dos formas de
      // responder a la misma pregunta.
      return Boolean(parte) && parte.semaforo === window.Pipeline.SEMAFORO_APROBADO;
    },

    destinoDeOrigen(parte) {
      // R37 · de dónde se rescató el parte, en castellano llano. Es la mitad
      // del texto que distingue esta marca del verde de siempre.
      const destino = (parte && parte.aprobacion && parte.aprobacion.destino_aprobado) || "";
      if (destino === "cola_validacion_humana") return "la cola de validación humana";
      if (destino === "revision_manual") return "revisión manual";
      return destino;
    },

    fechaDeAprobacion(parte) {
      // R37 · cuándo se aprobó. El backend la emite en UTC e ISO-8601; aquí se
      // enseña en la hora de quien mira, que es la que le sirve para saber si
      // fue hoy o el mes pasado.
      const momento = parte && parte.aprobacion && parte.aprobacion.aprobado_at_utc;
      if (!momento) {
        return "";
      }
      const fecha = new Date(momento);
      return isNaN(fecha.getTime()) ? String(momento) : fecha.toLocaleString("es-ES");
    },

    async aprobarParte() {
      // R29 · **sin segunda confirmación**: el botón es el acto explícito.
      // Aprobar no escribe en ningún sistema ajeno —escribe en el esquema
      // propio y se deshace revalidando—, y la confirmación única de F-025
      // sigue siendo la única que precede a una escritura externa.
      const parte = this.parteAbierto;
      this.mensajeAprobacion = "Registrando la aprobación…";
      try {
        const cuerpo = window.Pipeline.cuerpoDeAprobacion(parte, {
          remesaId: this.remesaId,
          usuarioOid: this.usuario.usuarioOid,
        });
        const datos = await api.aprobar(cuerpo, parte.hash);
        // Lo que se pinta es lo que dice el backend, no lo que suponga la
        // pantalla: quién decide si la aprobación sigue vigente es quien la
        // escribió (D-F).
        parte.aprobacion = datos.aprobacion;
        // `/api/aprobar` guarda el parte y su veredicto en la misma llamada
        // (`design.md` §6), así que a la vuelta consta guardado: dejarlo en
        // rojo lo mantendría fuera de la tanda por un fallo ya resuelto.
        parte.guardado = true;
        parte.errorGuardado = "";
        parte.semaforo = window.Pipeline.semaforoDe(
          parte.validacion,
          parte.aprobacion,
        );
        this.mensajeAprobacion =
          "Aprobado. Este parte entra en la tanda de archivo y cierre.";
      } catch (error) {
        this.mensajeAprobacion = (error && error.mensaje) || String(error);
      }
    },

    // =====================================================================
    // Archivar y cerrar, en una sola tanda (F-025; R19-R22, R25 de F-007)
    // =====================================================================
    pendientes() {
      // F-025 R24 · **un solo selector**, y vive en `js/pipeline.js`, que sí
      // tiene tests. Es más ancho que el `archivables()` que sustituye: trae
      // también los partes a medias —archivado sin adjuntar, adjuntado sin
      // cerrar—, que con los dos botones fundidos en uno se quedarían sin
      // ninguna forma de volver a entrar.
      //
      // F-019 R27 sigue dentro: «pendiente» incluye «ya guardado». Un parte
      // que no consta en la base recibiría un 409 y no subiría nada.
      return window.Pipeline.pendientesDeCircuito(this.partes);
    },

    noArchivables() {
      // Los que se leyeron bien y son aptos, pero no se pudieron guardar. Se
      // enseñan aparte y con su motivo: quedarse callado es lo que devuelve al
      // usuario al defecto 15.
      return this.partes.filter(
        (parte) =>
          !parte.archivado &&
          !parte.guardado &&
          window.Pipeline.esArchivable(parte.validacion),
      );
    },

    pedirConfirmacionArchivo() {
      // R19: confirmación explícita ANTES de la primera petición.
      this.confirmacionArchivo = window.Confirmacion.armar(Date.now());
      this.avisoArchivo = "";
    },

    confirmacionPendiente() {
      return window.Confirmacion.pendiente(this.confirmacionArchivo);
    },

    cancelarArchivo() {
      this.confirmacionArchivo = window.Confirmacion.cancelar();
      this.avisoArchivo = "";
    },

    async confirmarArchivo() {
      const decision = window.Confirmacion.resolver(
        this.confirmacionArchivo,
        Date.now(),
      );
      this.confirmacionArchivo = decision.estado;
      if (!decision.dispara) {
        this.avisoArchivo =
          decision.motivo === window.Confirmacion.CADUCADA
            ? window.Confirmacion.AVISO_CADUCADA
            : "";
        return;
      }
      this.avisoArchivo = "";

      const tanda = this.pendientes();
      if (!tanda.length) {
        return;
      }

      // F-025 R14 · la guarda de reentrada, y **envuelve la tanda entera**.
      // Si ya hay una corriendo, no se toca ni el estado de la pantalla: lo
      // que estuviera en curso sigue como estaba.
      const arranque = await window.Pipeline.conGuardaDeTanda(() =>
        this._lanzarTanda(tanda),
      );
      if (arranque.arrancada) {
        this.fase = "resumen";
      }
    },

    async _lanzarTanda(tanda) {
      // F-025 R7 · los tres pasos de cada parte, por la MISMA cola y con el
      // mismo límite de siempre (R11): fundir dos tandas en una no puede
      // multiplicar las peticiones simultáneas contra el ERP.
      this.entornoNoArchiva = "";
      this.entornoNoCierra = "";
      this.erpCerrado = false;
      this.tandaDetenida = false;
      this.fase = "archivando_y_cerrando";
      this.terminados = 0;
      this.totalTanda = tanda.length;
      await this._porLaCola(tanda, (parte) => this._circuitoDeUno(parte));
    },

    async _circuitoDeUno(parte) {
      // R22 · la puerta de entorno del archivo cerró la tanda. El corte se
      // mira **al empezar cada parte** porque cuando se levanta la bandera la
      // cola ya tiene los demás encolados.
      if (this.tandaDetenida) {
        return;
      }
      // Aquí no se decide nada: el orden de las tres escrituras, qué se salta
      // y qué se pide con `commit` es de `js/pipeline.js::ejecutarCircuito`,
      // que sí tiene tests (`tests_js/circuito.test.js`). Esto mueve estado de
      // Alpine y nada más, que es lo único que le toca a este fichero.
      const resultado = await window.Pipeline.ejecutarCircuito(parte, api, {
        usuarioOid: this.usuario.usuarioOid,
        correo: this.usuario.correo,
        // R21 · lo que sepamos AHORA de la ventana del ERP.
        //
        // Ojo con el alcance de esta bandera: la cola lanza hasta tres partes
        // a la vez, así que la ven los que aún no han arrancado, no los que ya
        // están en vuelo. Son como mucho dos respuestas de «servicio no
        // disponible» de más, y se acepta: cerrar la ventana a mitad de tanda
        // es el caso raro, y pararlo del todo exigiría cancelar peticiones ya
        // emitidas.
        erpCerrado: this.erpCerrado,
        alPaso: (paso) => {
          parte.paso = paso;
        },
      });
      // El paso se limpia pase lo que pase: uno congelado en «cerrando» diría
      // que sigue en marcha algo que ya terminó.
      parte.paso = "";
      this._aplicarResultado(parte, resultado);
    },

    _aplicarResultado(parte, resultado) {
      // `ejecutarCircuito` nunca lanza (R20): devuelve hasta dónde llegó, y
      // esto lo pinta. Un parte roto no tumba la tanda.
      parte.archivado = resultado.archivado;
      parte.grafico = resultado.grafico;

      if (resultado.archivo) {
        this.resultadosArchivo.push({
          hash: parte.hash,
          // La clave del `x-for`, y no vale el hash: un reintento empuja una
          // SEGUNDA fila del mismo parte, y dos filas con la misma clave hacen
          // que Alpine descarte una. La descartada sería la del reintento, que
          // es justo la que trae el resultado nuevo.
          clave: `${parte.hash}:${this.resultadosArchivo.length}`,
          mensaje: `${resultado.archivo.nombre_fichero} → ${resultado.archivo.carpeta} (${resultado.archivo.estado})`,
          web_url: resultado.archivo.web_url || "",
        });
      }

      if (resultado.tipoError === "entorno") {
        // La puerta de entorno NO es un fallo del parte: tiene pantalla propia
        // y el parte se queda como esté. Pintarlo en rojo llevaría a alguien a
        // «arreglar» una App Setting que está apagada a propósito.
        if (resultado.archivado) {
          parte.estado = "archivado";
        }
        this._anotarPuertaDeEntorno(resultado);
        return;
      }

      parte.cerrado = resultado.cerrado;
      parte.estado = resultado.estado;
      parte.error = resultado.error;

      if (resultado.mensaje) {
        this.resultadosCierre.push({
          hash: parte.hash,
          // Clave única por fila, no el hash (ver el resumen del archivo).
          // Aquí importa más: la fila que Alpine descartaría es la del
          // reintento, y con ella el número de incidencia de R37.
          clave: `${parte.hash}:${this.resultadosCierre.length}`,
          // R37 · el número de incidencia sobre el que se escribió. Se guarda
          // aparte del mensaje porque el resumen es **la primera y única
          // ocasión** en que quien pulsó puede ver que se escribió sobre la
          // incidencia equivocada: enterrarlo dentro de una frase lo esconde.
          incidencia: resultado.numeroIncidencia,
          mensaje: resultado.mensaje,
        });
      }
    },

    _anotarPuertaDeEntorno(resultado) {
      if (resultado.ambito === "archivo") {
        // R22 · sin archivo no hay nada que adjuntar ni que cerrar: los pasos
        // 2 y 3 responderían 409 por la puerta de archivo. La tanda se para.
        this.entornoNoArchiva = resultado.error;
        this.tandaDetenida = true;
        return;
      }
      // R21 · la ventana del ERP está cerrada. Los que queden siguen
      // archivando y no le piden nada al ERP, y el aviso se dice **una sola
      // vez**: es un campo de texto, no una lista, así que por muchos partes
      // que lo levanten en pantalla sale uno.
      this.erpCerrado = true;
      this.entornoNoCierra = resultado.error;
    },

    // =====================================================================
    // Cierre en Sigrid (F-009)
    // =====================================================================
    async cargarUsuario() {
      // Nunca falla hacia arriba: sin identidad el botón de cerrar se queda
      // deshabilitado —que es lo correcto, no se firma a nombre de nadie— y
      // el resto de la pantalla sigue sirviendo.
      this.usuario = await api.identidad();
    },

    cerrables() {
      // La decisión es de `js/pipeline.js`, que sí tiene tests: apto,
      // archivado y con número de incidencia. Aquí solo se filtra.
      return this.partes.filter(
        (parte) => !parte.cerrado && window.Pipeline.esCerrable(parte),
      );
    },

    async reintentarCierre(parte) {
      // R65 de F-012 · el estado «adjuntado pero no cerrado». El gráfico ya
      // está dentro de Sigrid, así que **no se vuelve a pedir**.
      //
      // F-025 · y no hace falta código aparte para conseguirlo: el reintento
      // pasa por el mismo circuito, que se salta archivar y adjuntar porque ya
      // constan hechos (R25, R26). Lo único que vuelve a viajar es el cierre;
      // el PDF no. Que se los salte lo fija `tests_js/circuito.test.js`.
      //
      // La confirmación ya se dio y sigue valiendo para este parte: es un
      // reintento de lo que se acaba de autorizar, no una tanda nueva.
      const arranque = await window.Pipeline.conGuardaDeTanda(() =>
        this._lanzarTanda([parte]),
      );
      if (arranque.arrancada) {
        this.fase = "resumen";
      }
    },

    // =====================================================================
    // Volver a empezar
    // =====================================================================
    reiniciar() {
      // F-026 R51 · lo primero, cortar el autoguardado en espera. Un
      // temporizador vivo después de reiniciar guardaría un parte que ya no
      // está en pantalla, contra una remesa que ya no existe.
      this._autoguardado().cancelarPendiente();
      this.estadoAutoguardado = "";
      this.mensajeAutoguardado = "";
      this._revocarPdf();
      this.fase = "inactivo";
      this.seleccion = [];
      this.mensajeDescartes = "";
      this.errorSeleccion = "";
      this.errorGlobal = "";
      this.avisosRemesa = [];
      this.partes = [];
      this.terminados = 0;
      this.remesaId = "";
      this.parteAbierto = null;
      this.confirmacionArchivo = window.Confirmacion.cancelar();
      this.avisoArchivo = "";
      this.entornoNoArchiva = "";
      this.resultadosArchivo = [];
      this.entornoNoCierra = "";
      this.resultadosCierre = [];
      // F-025 · el estado de la tanda. Arrastrar el total de la remesa
      // anterior dejaría la barra mintiendo, y arrastrar cualquiera de las dos
      // banderas dejaría la tanda nueva sin pedirle nada al ERP —o sin
      // arrancar siquiera— por una ventana que se cerró hace dos remesas.
      this.totalTanda = 0;
      this.erpCerrado = false;
      this.tandaDetenida = false;
    },
  };
}
