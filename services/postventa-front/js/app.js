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
