// services/postventa-front/js/portal_app.js
// F-035 · El componente de Alpine del portal (`design.md` §8.2): el estado de
// la pantalla y NADA MÁS. Misma regla de oro que `js/app.js`: **si algo
// merece un test, no vive aquí**. Cada método es una línea que mueve estado o
// delega en `js/portal.js` (lógica pura, probada) sobre `js/maqueta_datos.js`
// (los datos de ejemplo). La guardia de `tests/test_f035_portal.py` impide
// que se cuelen red, temporizadores, registro por consola o el cliente del
// circuito.
//
// La maqueta no sale de la pantalla (R14-R18): los placeholders solo ponen su
// aviso (R11, R12) y los controles locales solo navegan, filtran, seleccionan
// y abren o cierran paneles sobre los datos de ejemplo (D-6).
//
// En el HTML se monta con `x-data="portalPosventa()"` y `x-init="iniciar()"`:
// `iniciar()` lee la ruta del hash y se suscribe a `hashchange`, sin magias de
// Alpine, para que `tests_js/portal.test.js` lo instancie con un `window`
// falso (R16).

function portalPosventa() {
  const Portal = window.Portal;
  const datos = window.MaquetaDatos;
  const catalogos = datos.volcado.catalogos;
  const idsIncidencia = datos.incidencias.filas.map((fila) => fila.id);

  return {
    // Solo lectura, para los `x-for` del HTML.
    datos: datos,
    secciones: Portal.SECCIONES,
    estados: Portal.ESTADOS,

    // Dónde está el usuario (R4-R7).
    seccion: "inicio",
    incidenciaAbierta: null,
    pestanaFicha: "datos",
    avisoRuta: "",

    // Controles locales (R19, R20): se conservan al cambiar de sección.
    filtros: {
      incidencias: { estado: "", obra: "", texto: "" },
      bandeja: { origen: "", estado: "", obra: "" },
      impresion: { obra: "" },
    },
    seleccionIncidencias: [],
    seleccionBandeja: [],
    seleccionImpresion: [],
    filaBandejaAbierta: null,
    capituloAbierto: null,
    panelNoProcede: false,
    justificacion: "",

    // El aviso del último placeholder pulsado (R11): se queda hasta el siguiente.
    aviso: "",

    // ── Rutas ──────────────────────────────────────────────────────────────

    iniciar() {
      this.aplicarRuta();
      window.addEventListener("hashchange", () => this.aplicarRuta());
    },

    aplicarRuta() {
      const ruta = Portal.resolverRuta(window.location.hash, idsIncidencia);
      this.seccion = ruta.seccion;
      this.incidenciaAbierta = ruta.incidencia;
      this.avisoRuta = ruta.aviso || "";
      this.pestanaFicha = "datos";
      this.panelNoProcede = false;
    },

    ir(seccion, incidencia) {
      window.location.hash = Portal.hashDe(seccion, incidencia);
    },

    hashDe(seccion, incidencia) {
      return Portal.hashDe(seccion, incidencia);
    },

    // ── Placeholders (R11, R12) ────────────────────────────────────────────

    placeholder(id) {
      const selecciones = {
        incidencias: this.seleccionIncidencias,
        bandeja: this.seleccionBandeja,
        impresion: this.seleccionImpresion,
      };
      this.aviso = Portal.textoPlaceholder(id, { seleccionadas: Portal.seleccionadasPara(id, selecciones) });
    },

    // ── Listas filtradas (R19) ─────────────────────────────────────────────

    incidenciasFiltradas() {
      return Portal.filtrarIncidencias(datos.incidencias.filas, this.filtros.incidencias);
    },

    bandejaFiltrada() {
      return Portal.filtrarBandeja(datos.bandeja.filas, this.filtros.bandeja);
    },

    impresionFiltrada() {
      return Portal.filtrarIncidencias(datos.incidencias.filas, this.filtros.impresion);
    },

    incidenciasDelCapitulo() {
      return Portal.filtrarIncidencias(datos.incidencias.filas, { obra: this.capituloAbierto });
    },

    // ── Selección (R20) ────────────────────────────────────────────────────

    alternarIncidencia(id) {
      this.seleccionIncidencias = Portal.alternarSeleccion(this.seleccionIncidencias, id);
    },

    alternarBandeja(id) {
      this.seleccionBandeja = Portal.alternarSeleccion(this.seleccionBandeja, id);
    },

    alternarImpresion(id) {
      this.seleccionImpresion = Portal.alternarSeleccion(this.seleccionImpresion, id);
    },

    quitarSeleccionIncidencias() {
      this.seleccionIncidencias = [];
    },

    // ── Paneles y pestañas ─────────────────────────────────────────────────

    incidenciaActual() {
      return Portal.buscarPorId(datos.incidencias.filas, this.incidenciaAbierta);
    },

    verPestanaFicha(nombre) {
      this.pestanaFicha = nombre;
    },

    abrirNoProcede() {
      this.panelNoProcede = true;
    },

    cerrarNoProcede() {
      this.panelNoProcede = false;
    },

    filaBandeja() {
      return Portal.buscarPorId(datos.bandeja.filas, this.filaBandejaAbierta);
    },

    abrirFilaBandeja(id) {
      this.filaBandejaAbierta = id;
    },

    cerrarFilaBandeja() {
      this.filaBandejaAbierta = null;
    },

    abrirCapitulo(obra) {
      this.capituloAbierto = obra;
    },

    cerrarCapitulo() {
      this.capituloAbierto = null;
    },

    // ── Cómo se enseña cada dato (R21, R22, R39, R40) ──────────────────────

    contadores() {
      return Portal.contadoresInicio(datos);
    },

    etiquetaEstado(cod) {
      return Portal.etiquetaEstado(cod);
    },

    importe(valor) {
      return Portal.formatoImporte(valor);
    },

    obra(cod) {
      return Portal.etiquetaCatalogo(cod, datos.obras.filas);
    },

    tipo(cod) {
      return Portal.etiquetaCatalogo(cod, catalogos.tipos);
    },

    oficio(cod) {
      return Portal.etiquetaCatalogo(cod, catalogos.oficios);
    },

    forma(cod) {
      return Portal.etiquetaCatalogo(cod, catalogos.formas);
    },

    estadoVolcado(estado) {
      return Portal.etiquetaEstadoVolcado(estado, catalogos.estados);
    },

    resumenVolcado(resultado) {
      return Portal.resumenVolcado(resultado.partes);
    },

    propuesta(idFila) {
      return datos.propuestas.porFila[idFila] || null;
    },

    oficiosDeObra(obra) {
      return datos.propuestas.oficiosObra[obra] || [];
    },

    vinculo(idIncidencia) {
      return datos.vinculos.porIncidencia[idIncidencia] || null;
    },
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = portalPosventa;
}
