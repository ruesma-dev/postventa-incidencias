// services/postventa-front/js/app.js
// El estado de Alpine y NADA MÁS. Regla de oro del diseño (`design.md` §3):
// **si algo merece un test, no vive aquí**. Este fichero mueve estado de la
// pantalla y llama a los módulos, que son los que se prueban:
//
//   js/seleccion.js  qué entra en la remesa y cómo se envía  (R1-R4)
//   js/cola.js       el límite de concurrencia               (R7-R12)
//   js/api.js        timeout, reintentos, clasificación      (R23-R27)
//   js/pipeline.js   qué se pide, en qué orden y qué viaja   (R8, R13-R22)
//   js/confirmacion.js  el doble clic antes de archivar y de
//                       cerrar                                (R19, F-009 R15)
//   js/traza.js      el único registro permitido             (R28)
//
// Aquí no hay ni un bucle de reintento, ni un cálculo de veredicto, ni una
// composición de cuerpo de petición. Si aparece alguno, está en el sitio
// equivocado.

function appPostventa() {
  const config = window.CONFIG_POSTVENTA;
  const api = window.Api.crearApi({ baseApi: config.baseApi, config: config });

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
    CAMPOS: window.Pipeline.CAMPOS_DEL_PARTE,

    // --- archivo (R19-R22, R25) ---
    // El estado de la confirmación lo compone `js/confirmacion.js`: aquí solo
    // se guarda lo que devuelve, sin interpretarlo.
    confirmacionArchivo: null,
    avisoArchivo: "",
    entornoNoArchiva: "",
    resultadosArchivo: [],

    // --- cierre en Sigrid (F-009) ---
    // Quién dice ser el usuario, para poder firmar el cierre en el ERP. Lo
    // sirve el proxy de la Static Web App y NO está firmado: es una traza de
    // quién lo pidió, no un control de acceso. Con quién se firma de verdad lo
    // decide el ERP, que tiene que confirmar el login antes de escribir nada.
    usuario: { usuarioOid: "", correo: "" },
    // El dry-run de cada parte, por `hash`. Es lo que hay que enseñar ANTES de
    // que nadie confirme: los dos estados legibles, con qué login se firmaría
    // y el aviso de que la reclamación quedará cerrada sin el parte dentro de
    // Sigrid. Confirmar sin haberlo leído es lo que esto viene a evitar.
    dryRunCierre: {},
    confirmacionCierre: null,
    avisoCierre: "",
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
        extraccion: null,
        firma: null,
        validacion: null,
        ediciones: {},
        archivado: false,
        // F-019 R27: hasta que conste guardado, el parte no es archivable.
        guardado: false,
        errorGuardado: "",
      };
    },

    // =====================================================================
    // Proceso parte a parte, por la cola (R7-R12)
    // =====================================================================
    async _procesarRemesa() {
      this.fase = "procesando";
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
    },

    _anotarVeredicto(parte, validacion) {
      parte.validacion = validacion;
      parte.semaforo = window.Pipeline.semaforoDe(validacion);
      parte.estado = "listo";
    },

    async reintentarParte(parte) {
      // R11: el reintento pasa por la misma cola y respeta el mismo límite.
      this.terminados = Math.max(0, this.terminados - 1);
      await this._porLaCola([parte], (uno) => this._procesarUno(uno));
    },

    porcentaje() {
      return this.partes.length
        ? Math.round((this.terminados / this.partes.length) * 100)
        : 0;
    },

    tituloDeFase() {
      if (this.fase === "troceando") return "Troceando la remesa";
      if (this.fase === "archivando") return "Archivando";
      return "Procesando los partes";
    },

    // =====================================================================
    // Detalle, edición y revalidación (R14-R18)
    // =====================================================================
    abrirParte(parte) {
      this._revocarPdf();
      this.parteAbierto = parte;
      this.mensajeRevalidacion = "";
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
    },

    hayEdiciones() {
      return (
        this.parteAbierto && Object.keys(this.parteAbierto.ediciones).length > 0
      );
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
    // Archivo (R19-R22, R25)
    // =====================================================================
    archivables() {
      // F-019 R27: «archivable» incluye «ya guardado». Un parte que no consta
      // en la base recibiría un 409 y no subiría nada; ofrecerlo sería
      // prometer algo que el backend va a rechazar.
      return this.partes.filter(
        (parte) =>
          !parte.archivado &&
          parte.guardado &&
          window.Pipeline.esArchivable(parte.validacion),
      );
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

      const pendientes = this.archivables();
      if (!pendientes.length) {
        return;
      }

      this.entornoNoArchiva = "";
      this.fase = "archivando";
      this.terminados = 0;
      await this._porLaCola(pendientes, (parte) => this._archivarUno(parte));
      this.fase = "resumen";
    },

    async _archivarUno(parte) {
      try {
        // cuerpoDeArchivo se niega a componer nada que no sea apto (R21).
        const datos = await api.archivar(
          window.Pipeline.cuerpoDeArchivo(parte),
          parte.hash,
        );
        parte.archivado = true;
        parte.estado = "archivado";
        this.resultadosArchivo.push({
          hash: parte.hash,
          mensaje: `${datos.nombre_fichero} → ${datos.carpeta} (${datos.estado})`,
          web_url: datos.web_url || "",
        });
      } catch (error) {
        if (error && error.tipo === "entorno") {
          // R25: pantalla propia. NO es un fallo y no se toca la puerta de
          // entorno del backend para «arreglarlo».
          this.entornoNoArchiva = error.mensaje;
          return;
        }
        parte.estado = "error_archivo";
        parte.error = (error && error.mensaje) || String(error);
      }
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

    puedeCerrar() {
      return Boolean(this.usuario.usuarioOid) && this.cerrables().length > 0;
    },

    async pedirDryRunCierre() {
      // R8 · el dry-run va PRIMERO y por su cuenta: se pide sin `commit`, así
      // que esta tanda no escribe nada en el ERP pase lo que pase.
      this.avisoCierre = "";
      this.entornoNoCierra = "";
      this.confirmacionCierre = window.Confirmacion.cancelar();
      this.fase = "dry_run";
      await this._porLaCola(this.cerrables(), (parte) => this._dryRunUno(parte));
      this.fase = "resumen";
    },

    async _dryRunUno(parte) {
      try {
        const datos = await api.cerrar(
          window.Pipeline.cuerpoDeCierre(parte, this.usuario),
          parte.hash,
        );
        this.dryRunCierre[parte.hash] = datos.dry_run;
        if (datos.estado === "ya_cerrada") {
          // R18 · no es un error: la incidencia ya estaba cerrada antes de que
          // llegáramos. Se saca de la lista de cerrables y **se dice**: si
          // desapareciera en silencio, quien mira la pantalla creería que se
          // ha perdido un parte.
          parte.cerrado = true;
          parte.estado = "ya_cerrada";
          this.resultadosCierre.push({
            hash: parte.hash,
            mensaje: `${datos.numero_incidencia} ya estaba cerrada en Sigrid: no se ha tocado nada`,
          });
        }
      } catch (error) {
        this._anotarFalloDeCierre(parte, error);
      }
    },

    hayDryRun() {
      return Object.keys(this.dryRunCierre).length > 0;
    },

    dryRunDe(parte) {
      return this.dryRunCierre[parte.hash] || null;
    },

    pedirConfirmacionCierre() {
      // R15 · la confirmación explícita, con su ventana, ANTES de la primera
      // escritura. La compone `js/confirmacion.js`, que sí tiene tests.
      this.confirmacionCierre = window.Confirmacion.armar(Date.now());
      this.avisoCierre = "";
    },

    confirmacionCierrePendiente() {
      return window.Confirmacion.pendiente(this.confirmacionCierre);
    },

    cancelarCierre() {
      this.confirmacionCierre = window.Confirmacion.cancelar();
      this.avisoCierre = "";
    },

    async confirmarCierre() {
      const decision = window.Confirmacion.resolver(
        this.confirmacionCierre,
        Date.now(),
      );
      this.confirmacionCierre = decision.estado;
      if (!decision.dispara) {
        this.avisoCierre =
          decision.motivo === window.Confirmacion.CADUCADA
            ? window.Confirmacion.avisoCaducada("cierre")
            : "";
        return;
      }
      this.avisoCierre = "";

      const pendientes = this.cerrables().filter((parte) => this.dryRunDe(parte));
      if (!pendientes.length) {
        return;
      }

      this.entornoNoCierra = "";
      this.fase = "cerrando";
      this.terminados = 0;
      await this._porLaCola(pendientes, (parte) => this._cerrarUno(parte));
      this.fase = "resumen";
    },

    async _cerrarUno(parte) {
      try {
        const datos = await api.cerrar(
          window.Pipeline.cuerpoDeCierre(
            parte,
            Object.assign({ commit: true, confirmado: true }, this.usuario),
          ),
          parte.hash,
        );
        parte.cerrado = true;
        parte.estado = datos.estado;
        this.resultadosCierre.push({
          hash: parte.hash,
          mensaje: `${datos.numero_incidencia} → ${datos.estado}`,
        });
      } catch (error) {
        this._anotarFalloDeCierre(parte, error);
      }
    },

    _anotarFalloDeCierre(parte, error) {
      if (error && error.tipo === "entorno") {
        // Pantalla propia: es la puerta de entorno del cierre, no un fallo, y
        // no se toca para «arreglarlo». Lo que hay detrás es el ERP.
        this.entornoNoCierra = error.mensaje;
        return;
      }
      parte.estado = "error_cierre";
      parte.error = (error && error.mensaje) || String(error);
    },

    // =====================================================================
    // Volver a empezar
    // =====================================================================
    reiniciar() {
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
      this.confirmacionCierre = window.Confirmacion.cancelar();
      this.avisoCierre = "";
      this.entornoNoCierra = "";
      this.resultadosCierre = [];
      this.dryRunCierre = {};
    },
  };
}
