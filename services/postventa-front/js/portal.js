// services/postventa-front/js/portal.js
// F-035 · La lógica del portal de posventa (`design.md` §8.1).
//
// PURO: catálogos y funciones sin DOM, sin Alpine y sin red. Es lo que hace
// que se pruebe con `node --test` sin navegador (`tests_js/portal.test.js`);
// el componente de Alpine (`js/portal_app.js`) solo delega aquí.
//
//   SECCIONES      las ocho pestañas de la barra superior, en su orden (R2),
//                  cada una con su estado (R62)
//   PAGINAS        las páginas reales de una sección, con su sección (R17, §16.8)
//   RECORRIDO      los siete pasos del ciclo de una incidencia, la tira bajo la
//                  barra de las cinco páginas (R83, §16.16)
//   PLACEHOLDERS   las acciones sin construir, con la ficha que las hará (R8)
//   ESTADOS        los cinco estados de conest, por código y resumen (R21)
//   resolverRuta / hashDe / enlaceSeccion   rutas por hash y enlaces (R4-R7, R31, R44, R46, R70)
//   enConstruccion                          si una sección está en construcción (R62, R66)
//   marcadaEnConstruccion                   si su pestaña o su paso llevan la marca (R66, R87; F-040 T6a)
//   pasoDeSeccion                           el paso de la tira que marca una sección (R83, R86)
//   fichasDeSeccion                         las fichas que nombra su rótulo (R65)
//   textoPlaceholder / seleccionadasPara    el aviso de un placeholder (R11, R12)
//   filtrarIncidencias / alternarSeleccion                    solo en pantalla (R19, R20)
//   etiquetaEstado / formatoImporte / etiquetaCatalogo        cómo se enseña (R21, R22, R39)
//   buscarPorId                                               abrir una ficha o un detalle (R6)
//
// La regla de retirada (`design.md` §7.3): cuando una ficha F-0NN construya su
// pieza, borra aquí sus entradas de PLACEHOLDERS en el mismo trabajo. Cada
// entrada lleva su `ficha: "F-0NN"` escrita literal, que es lo que lee la
// guardia de la raíz (`tests/test_f035_placeholders_vivos.py`, R27-R29).

(function () {
  "use strict";

  function congelarLista(lista) {
    lista.forEach(function (elemento) {
      Object.freeze(elemento);
      if (Array.isArray(elemento.fichas)) Object.freeze(elemento.fichas);
    });
    return Object.freeze(lista);
  }

  // ── Catálogos ─────────────────────────────────────────────────────────────

  /**
   * Las secciones del portal (`design.md` §4). `pagina` es `null` para las
   * siete que viven en el portal (`index.html`, rutas `#/<id>`) y
   * `"partes.html"` para `partes`, que ES el circuito (D-1, D-3).
   *
   * `estado` (R62, `design.md` §16.4): `"real"`, `"parcial"` o
   * `"construccion"`, escrito LITERAL porque lo lee como texto la guardia de
   * la raíz (`tests/test_f035_placeholders_vivos.py`), que lo compara con las
   * fichas de `harness/features.json`: cuando una ficha pasa a `done`, el
   * estado de su sección se cambia aquí en el mismo trabajo.
   *
   * `enlace` (F-040 T6a, decisión del humano del 2026-11-04): la página real
   * a la que llevan la pestaña, los pasos de la tira y la tarjeta de una
   * sección que vive en el portal, en vez de su ruta `#/<id>` de la maqueta;
   * `null` = su ruta. Hoy solo `bandeja` → `bandeja.html`. La ruta `#/bandeja`
   * sigue existiendo (`resolverRuta`): solo deja de enlazarse desde ahí. El
   * `estado` no lo da el enlace sino las fichas (R62): `bandeja` pasó a
   * `parcial` en el cierre de F-038 (R17 de F-038), la primera de sus fichas
   * en `done`.
   */
  const SECCIONES = congelarLista([
    { id: "inicio", etiqueta: "Inicio", fichas: [], pagina: null, enlace: null, estado: "parcial" },
    { id: "entrada", etiqueta: "Entrada", fichas: ["F-036", "F-037"], pagina: null, enlace: null, estado: "parcial" },
    { id: "bandeja", etiqueta: "Bandeja de revisión", fichas: ["F-038", "F-039", "F-040", "F-043"], pagina: null, enlace: "bandeja.html", estado: "parcial" },
    { id: "incidencias", etiqueta: "Incidencias", fichas: ["F-041", "F-042", "F-043", "F-047"], pagina: null, enlace: null, estado: "construccion" },
    { id: "impresion", etiqueta: "Impresión de partes", fichas: ["F-044"], pagina: null, enlace: null, estado: "construccion" },
    { id: "partes", etiqueta: "Partes firmados", fichas: ["F-045"], pagina: "partes.html", enlace: null, estado: "parcial" },
    { id: "economico", etiqueta: "Coste y venta", fichas: ["F-046", "F-047"], pagina: null, enlace: null, estado: "construccion" },
    { id: "datos", etiqueta: "Datos y datamart", fichas: ["F-048"], pagina: null, enlace: null, estado: "construccion" },
  ]);

  /**
   * Las páginas reales que son parte de una sección del portal, con su
   * sección (`design.md` §16.2 y §16.8): funcionan de verdad, hablan con el
   * backend desde sus propios módulos y no cargan nada de la maqueta. El
   * portal puede enlazarlas, en la misma ventana y con un ancla opcional
   * (R17, enmienda del 2026-10-05). `partes.html` no está aquí: es la sección
   * `partes` entera (su `pagina` en SECCIONES). `bandeja.html` es la página de
   * revisión de F-038 (su R1), la primera real de `bandeja`.
   */
  const PAGINAS = Object.freeze({
    "importar.html": "entrada",
    "oficios.html": "entrada",
    "bandeja.html": "bandeja",
  });

  /**
   * El ciclo de una incidencia, la tira bajo la barra de las cinco páginas
   * (R83-R87, design.md §16.16). `seccion` es la de Portal.SECCIONES a la que
   * lleva el paso; el enlace sale de enlaceSeccion(seccion, desde). 02 y 03
   * van a la misma sección (la bandeja): el actual es el PRIMERO
   * (pasoDeSeccion), así que 03 no se marca mientras no tenga sitio propio.
   * En `bandeja.html` (F-038, R25) el 03 es un <span> sin enlace ni
   * aria-current: es de la sección de la página, pero no es el paso actual.
   */
  const RECORRIDO = congelarLista([
    { num: "01", etiqueta: "Entrada", seccion: "entrada" },
    { num: "02", etiqueta: "Revisión", seccion: "bandeja" },
    { num: "03", etiqueta: "Sigrid", seccion: "bandeja" },
    { num: "04", etiqueta: "Gestión", seccion: "incidencias" },
    { num: "05", etiqueta: "Parte", seccion: "impresion" },
    { num: "06", etiqueta: "Cierre", seccion: "partes" },
    { num: "07", etiqueta: "Coste", seccion: "economico" },
  ]);

  /**
   * El título de cada ficha del ciclo, tal como está en `harness/features.json`,
   * para el aviso de R11 («lo construye F-0NN · <título>») y para el rótulo de
   * los recuadros «En construcción» (R65, `fichasDeSeccion`). La maqueta no
   * lee `features.json`: por eso se copia aquí. Solo guarda las fichas por
   * construir: la que se cierra borra aquí su título en el mismo trabajo, y la
   * última borra también este mapa (`design.md` §7.3).
   */
  const TITULOS_FICHAS = Object.freeze({
    "F-037": "Entrada desde la web de clientes: el contrato con el proyecto independiente",
    "F-039": "Propuesta del industrial al crear la incidencia",
    "F-041": "Ficha de la incidencia: cambiar estado y modificar campos como en Sigrid",
    "F-042": "No procede: justificación obligatoria y email al cliente",
    "F-043": "Operaciones en bloque sobre incidencias",
    "F-044": "Imprimir partes en bloque a PDF o impresora con la plantilla de posventa",
    "F-045": "Registrar un parte sin firma: la incidencia pasa a TER, no a CER",
    "F-046": "Coste de la posventa desde la obra POSTV2",
    "F-047": "Vincular incidencias con la proforma, el coste y la venta",
    "F-048": "Los datos de posventa al datamart",
  });

  /**
   * Las acciones que todavía no existen (`design.md` §6.3, con la enmienda del
   * 2026-09-25). El prefijo del `id` es la sección de la que es la acción, no
   * el bloque donde se pinta: `partes.registrarSinFirma` se dibuja en la
   * tarjeta «Partes firmados» de `inicio` (D-7). `enBloque` marca las que
   * dicen a cuántas afectarían con la selección actual (R12). Desde el cierre
   * de F-038 (`design.md` §3.2 de F-038) `#/bandeja` ya no tiene filas que
   * seleccionar: `bandeja.aprobarSeleccionadas` pasó a `enBloque: false`. Con
   * el de F-040 (`design.md` §4 de F-040) salieron sus tres entradas
   * (`bandeja.verVolcado`, `bandeja.volcar` y `bandeja.reintentarVolcado`):
   * el volcado es el panel de `bandeja.html`.
   */
  const PLACEHOLDERS = congelarLista([
    {
      id: "entrada.verContratoWeb",
      ficha: "F-037",
      etiqueta: "Ver el contrato de entrada",
      explicacion: "Enseñará el contrato con el que la web de clientes dejará sus incidencias en la misma bandeja, con origen «Web».",
      enBloque: false,
    },
    {
      id: "bandeja.cambiarIndustrial",
      ficha: "F-039",
      etiqueta: "Cambiar industrial",
      explicacion: "Permitirá elegir otro industrial, entre los oficios de la obra con su proveedor, en lugar del propuesto.",
      enBloque: false,
    },
    {
      id: "bandeja.aprobarSeleccionadas",
      ficha: "F-043",
      etiqueta: "Aprobar las seleccionadas",
      explicacion: "Aprobará de una vez todas las filas marcadas de la bandeja.",
      enBloque: false,
    },
    {
      id: "incidencias.cambiarEstadoBloque",
      ficha: "F-043",
      etiqueta: "Cambiar estado…",
      explicacion: "Cambiará el estado de las incidencias marcadas, con un ensayo previo que dice qué cambiaría en Sigrid.",
      enBloque: true,
    },
    {
      id: "incidencias.asignarIndustrialBloque",
      ficha: "F-043",
      etiqueta: "Asignar industrial…",
      explicacion: "Asignará el mismo industrial a todas las incidencias marcadas.",
      enBloque: true,
    },
    {
      id: "incidencias.imprimirBloque",
      ficha: "F-044",
      etiqueta: "Imprimir los partes",
      explicacion: "Generará el PDF de los partes de las incidencias marcadas con la plantilla de posventa.",
      enBloque: true,
    },
    {
      id: "ficha.guardar",
      ficha: "F-041",
      etiqueta: "Guardar cambios",
      explicacion: "Guardará en Sigrid los campos modificados de la incidencia, con histórico de cada cambio.",
      enBloque: false,
    },
    {
      id: "ficha.verCambioEstado",
      ficha: "F-041",
      etiqueta: "Ver qué cambiaría en Sigrid",
      explicacion: "Enseñará qué cambiaría en Sigrid al pasar la incidencia al estado elegido, sin cambiar nada.",
      enBloque: false,
    },
    {
      id: "ficha.aplicarEstado",
      ficha: "F-041",
      etiqueta: "Aplicar el cambio",
      explicacion: "Aplicará en Sigrid el cambio de estado elegido y lo dejará en el historial.",
      enBloque: false,
    },
    {
      id: "ficha.cambiarIndustrial",
      ficha: "F-039",
      etiqueta: "Cambiar industrial",
      explicacion: "Permitirá elegir otro industrial para esta incidencia entre los oficios de su obra con su proveedor.",
      enBloque: false,
    },
    {
      id: "ficha.imprimir",
      ficha: "F-044",
      etiqueta: "Imprimir el parte",
      explicacion: "Generará el PDF del parte de esta incidencia con la plantilla de posventa.",
      enBloque: false,
    },
    {
      id: "ficha.enviarNoProcede",
      ficha: "F-042",
      etiqueta: "Pasar a no procede y enviar el correo",
      explicacion: "Pasará la incidencia a NO PROCEDE con la justificación escrita y enviará el correo al cliente. En pruebas nunca sale un correo a un cliente real.",
      enBloque: false,
    },
    {
      id: "ficha.registrarSinFirma",
      ficha: "F-045",
      etiqueta: "Registrar el parte sin firma",
      explicacion: "Registrará el parte sin firma: la incidencia quedará en TER, no en CER. Exigirá confirmación expresa y quedará constancia de quién.",
      enBloque: false,
    },
    {
      id: "ficha.enlazarProforma",
      ficha: "F-047",
      etiqueta: "Enlazar proforma",
      explicacion: "Enlazará la incidencia con su proforma para ver juntos su coste y su venta.",
      enBloque: false,
    },
    {
      id: "impresion.generarPdf",
      ficha: "F-044",
      etiqueta: "Generar el PDF",
      explicacion: "Generará un PDF con los partes marcados, con la plantilla de posventa.",
      enBloque: true,
    },
    {
      id: "impresion.imprimir",
      ficha: "F-044",
      etiqueta: "Imprimir",
      explicacion: "Enviará a la impresora los partes marcados.",
      enBloque: true,
    },
    {
      id: "partes.registrarSinFirma",
      ficha: "F-045",
      etiqueta: "Registrar un parte sin firma",
      explicacion: "Registrará un parte sin firma: la incidencia quedará en TER, no en CER, con confirmación expresa y constancia de quién. No toca el circuito de partes firmados.",
      enBloque: false,
    },
    {
      id: "economico.actualizar",
      ficha: "F-046",
      etiqueta: "Actualizar desde Sigrid",
      explicacion: "Leerá de Sigrid el coste de cada capítulo de la obra POSTV2.",
      enBloque: false,
    },
    {
      id: "datos.verDiccionario",
      ficha: "F-048",
      etiqueta: "Ver el diccionario en el datamart",
      explicacion: "Abrirá el diccionario del datamart con lo que publica cada fase de posventa.",
      enBloque: false,
    },
  ]);

  /** Estados de conest para partes de reclamación, por código (R21). */
  const ESTADOS = congelarLista([
    { cod: "SAT", res: "SIN ATENDER" },
    { cod: "PTE", res: "PENDIENTE" },
    { cod: "TER", res: "TERMINADA" },
    { cod: "NPR", res: "NO PROCEDE" },
    { cod: "CER", res: "CERRADA" },
  ]);

  const SECCION_POR_DEFECTO = "inicio";
  const AVISO_INCIDENCIA_INEXISTENTE = "Esa incidencia no existe en los datos de ejemplo";
  const TEXTO_PLACEHOLDER_DESCONOCIDO =
    "Todavía no hace nada: esta acción está en construcción.";
  const TEXTO_TIPO_PENDIENTE = "Pendiente: qué es y cuándo se usa";
  const SIN_COMPLETAR = "sin completar";
  const SIN_ENLAZAR = "sin enlazar";

  // ── Rutas ─────────────────────────────────────────────────────────────────

  /** La sección del catálogo con ese id, o `null`. */
  function seccionPorId(id) {
    return SECCIONES.find(function (s) { return s.id === id; }) || null;
  }

  /**
   * `#/<id>` y `#/incidencias/<id>` → qué enseñar (R4-R7). Tolera `""`, `"#"`,
   * `"#/"`, mayúsculas y la barra final. Una sección que no vive en el portal
   * (`pagina` distinta de `null`: `partes`) cuenta como desconocida (R5).
   */
  function resolverRuta(hash, idsIncidencia) {
    const partes = String(hash || "")
      .replace(/^#/, "")
      .split("/")
      .filter(function (trozo) { return trozo !== ""; });
    const seccion = seccionPorId(String(partes[0] || "").toLowerCase());

    if (!seccion || seccion.pagina !== null) {
      return { seccion: SECCION_POR_DEFECTO, incidencia: null, aviso: null };
    }
    if (seccion.id === "incidencias" && partes.length > 1) {
      const buscado = String(partes[1]).toLowerCase();
      const encontrado = (idsIncidencia || []).find(function (id) {
        return String(id).toLowerCase() === buscado;
      });
      if (encontrado === undefined) {
        return { seccion: "incidencias", incidencia: null, aviso: AVISO_INCIDENCIA_INEXISTENTE };
      }
      return { seccion: "incidencias", incidencia: encontrado, aviso: null };
    }
    return { seccion: seccion.id, incidencia: null, aviso: null };
  }

  /** La inversa de `resolverRuta`: la ruta de una sección o de una ficha. */
  function hashDe(seccion, incidencia) {
    return incidencia ? "#/" + seccion + "/" + incidencia : "#/" + seccion;
  }

  /**
   * El enlace de una pestaña de la barra superior (R31, R44, R46): la ÚNICA
   * fuente de los `href` de las dos barras.
   *
   * - Desde el portal: `#/<id>` y, para `partes`, `partes.html`; siempre en
   *   la misma pestaña del navegador (la maqueta no tiene nada que perder).
   * - Desde el circuito: `./#/<id>`, también en la misma pestaña (ajuste
   *   del 2026-10-05, R31): la remesa en curso la protege la guarda de
   *   salida (`js/guarda_salida.js`, R78); `partes` es la página actual →
   *   `null`.
   * - Desde una página real (una clave de PAGINAS, `design.md` §16.8): la
   *   sección de la página es la actual → `null`; `partes` → `partes.html`;
   *   las demás → `./#/<id>`. Todo en la misma pestaña (R70, R73).
   * - Una sección con `enlace` (F-040 T6a: `bandeja`) lleva a esa página
   *   desde los tres sitios, salvo desde la propia página (`null`).
   *
   * Un id o un `desde` desconocidos → `null`, nunca lanza.
   */
  function enlaceSeccion(id, desde) {
    const seccion = seccionPorId(id);
    if (!seccion) return null;
    if (desde === "portal") {
      return { href: seccion.pagina || seccion.enlace || hashDe(seccion.id), nuevaPestana: false };
    }
    if (desde === "circuito") {
      if (seccion.pagina !== null) return null;
      return { href: seccion.enlace || "./" + hashDe(seccion.id), nuevaPestana: false };
    }
    if (typeof desde === "string" && Object.prototype.hasOwnProperty.call(PAGINAS, desde)) {
      if (seccion.id === PAGINAS[desde]) return null;
      return { href: seccion.pagina || seccion.enlace || "./" + hashDe(seccion.id), nuevaPestana: false };
    }
    return null;
  }

  /**
   * Si la sección está en construcción (R62): su `estado` es
   * `"construccion"`. Es lo que marca su pestaña en las barras (R66). Un id
   * desconocido, vacío o que no es texto → `false`, nunca lanza.
   */
  function enConstruccion(id) {
    const seccion = seccionPorId(id);
    return seccion !== null && seccion.estado === "construccion";
  }

  /**
   * Si la pestaña o el paso de esa sección, vistos desde `desde` (el de
   * `enlaceSeccion`), llevan la marca de construcción (R66, R87). F-040 T6a:
   * la marca avisa de que se va a la maqueta; un enlace a la página real de
   * la sección (`enlace`) no la lleva aunque la sección siga en
   * construcción. Sin enlace —la pestaña actual de esa página, o un `desde`
   * desconocido—, la de la sección (R2 y R25 de F-038). Nunca lanza.
   */
  function marcadaEnConstruccion(id, desde) {
    if (!enConstruccion(id)) return false;
    const enlace = enlaceSeccion(id, desde);
    return enlace === null || enlace.href !== seccionPorId(id).enlace;
  }

  /** El num del primer paso de esa sección, o null; nunca lanza (R83). */
  function pasoDeSeccion(id) {
    const paso = RECORRIDO.find(function (p) { return p.seccion === id; });
    return paso ? paso.num : null;
  }

  /**
   * Las fichas que nombra el rótulo del recuadro «En construcción» de una
   * sección (R65, `design.md` §16.4): «La construirán: F-0NN · <título>».
   * Las de su entrada de SECCIONES, en su orden, que tienen título en
   * TITULOS_FICHAS; una ficha ya hecha no lo tiene (su título se borra al
   * cerrarla, §7.3) y no se nombra. Lista nueva en cada llamada; un id
   * desconocido → `[]`, nunca lanza.
   */
  function fichasDeSeccion(id) {
    const seccion = seccionPorId(id);
    if (!seccion) return [];
    return seccion.fichas
      .filter(function (ficha) { return Object.prototype.hasOwnProperty.call(TITULOS_FICHAS, ficha); })
      .map(function (ficha) { return { ficha: ficha, titulo: TITULOS_FICHAS[ficha] }; });
  }

  // ── Placeholders ──────────────────────────────────────────────────────────

  function placeholderPorId(id) {
    return PLACEHOLDERS.find(function (p) { return p.id === id; }) || null;
  }

  /**
   * Cuántos elementos marcados cuenta un placeholder en bloque (R12): la
   * selección de la sección de su prefijo (`incidencias.*`, `impresion.*`;
   * `bandeja.*` ya no tiene selección desde el cierre de F-038). Cualquier
   * otro, cero.
   */
  function seleccionadasPara(id, selecciones) {
    const prefijo = String(id || "").split(".")[0];
    const lista = selecciones && Object.prototype.hasOwnProperty.call(selecciones, prefijo)
      ? selecciones[prefijo]
      : null;
    return Array.isArray(lista) ? lista.length : 0;
  }

  /**
   * El aviso de un placeholder (R11): «Todavía no hace nada: lo construye
   * F-0NN · <título de la ficha>.» con la frase del catálogo; y, si es una
   * operación en bloque, a cuántas incidencias afectaría (R12). Un id
   * desconocido da un texto genérico: nunca lanza.
   */
  function textoPlaceholder(id, contexto) {
    const p = placeholderPorId(id);
    if (!p) return TEXTO_PLACEHOLDER_DESCONOCIDO;

    const titulo = TITULOS_FICHAS[p.ficha] || p.etiqueta;
    let texto = "Todavía no hace nada: lo construye " + p.ficha + " · " + titulo + ". " + p.explicacion;
    if (p.enBloque) {
      const n = Number((contexto && contexto.seleccionadas) || 0);
      texto += " Con la selección actual afectaría a " + n + (n === 1 ? " incidencia." : " incidencias.");
    }
    return texto;
  }

  // ── Filtros y selección (solo en pantalla) ────────────────────────────────

  /** Minúsculas y sin tildes, para buscar texto como lo escribe una persona. */
  function normalizar(texto) {
    return String(texto || "")
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .toLowerCase();
  }

  /** R19: estado, obra y texto (código y descripciones), todos a la vez. */
  function filtrarIncidencias(filas, filtros) {
    const f = filtros || {};
    const texto = normalizar(f.texto).trim();
    return (filas || []).filter(function (fila) {
      if (f.estado && fila.estado !== f.estado) return false;
      if (f.obra && fila.obra !== f.obra) return false;
      if (texto) {
        const donde = [fila.cod, fila.descripcionCorta, fila.descripcionLarga].map(normalizar).join("\n");
        if (donde.indexOf(texto) === -1) return false;
      }
      return true;
    });
  }

  /** R20: marca o desmarca; devuelve una lista nueva, no muta la de entrada. */
  function alternarSeleccion(seleccion, id) {
    const actual = seleccion || [];
    if (actual.indexOf(id) !== -1) {
      return actual.filter(function (x) { return x !== id; });
    }
    return actual.concat([id]);
  }

  /** La fila con ese `id`, o `null` (abrir una ficha o un detalle). */
  function buscarPorId(filas, id) {
    if (id === null || id === undefined) return null;
    return (filas || []).find(function (fila) { return fila.id === id; }) || null;
  }

  // ── Cómo se enseña ────────────────────────────────────────────────────────

  /** R21: «PTE · PENDIENTE»; un código desconocido, tal cual. */
  function etiquetaEstado(cod) {
    const estado = ESTADOS.find(function (e) { return e.cod === cod; });
    return estado ? estado.cod + " · " + estado.res : String(cod);
  }

  /**
   * R22: un importe en formato es-ES con «€», y lo no enlazado como «sin
   * enlazar», NUNCA como «0,00 €». Se formatea a mano, y no con `Intl`, para
   * que el navegador y `node --test` den exactamente lo mismo (es-ES en
   * `Intl` no agrupa los miles de cuatro cifras: «1250,00 €»).
   */
  function formatoImporte(valor) {
    if (valor === null || valor === undefined) return SIN_ENLAZAR;
    const numero = Number(valor);
    if (!Number.isFinite(numero)) return SIN_ENLAZAR;
    const trozos = Math.abs(numero).toFixed(2).split(".");
    const entero = trozos[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return (numero < 0 ? "-" : "") + entero + "," + trozos[1] + " €";
  }

  /**
   * R39: una entrada de catálogo `{cod, res}` como «código · resumen». Sin
   * resumen (el tipo 0003) → su pendiente, sin inventarlo; sin código →
   * «sin completar»; código que no está en el catálogo → tal cual.
   */
  function etiquetaCatalogo(cod, catalogo) {
    if (cod === null || cod === undefined || cod === "") return SIN_COMPLETAR;
    const entrada = (catalogo || []).find(function (e) { return String(e.cod) === String(cod); });
    if (!entrada) return String(cod);
    if (entrada.res === null || entrada.res === undefined) return entrada.cod + " · " + TEXTO_TIPO_PENDIENTE;
    return entrada.cod + " · " + entrada.res;
  }

  const Portal = {
    SECCIONES: SECCIONES,
    PAGINAS: PAGINAS,
    RECORRIDO: RECORRIDO,
    PLACEHOLDERS: PLACEHOLDERS,
    ESTADOS: ESTADOS,
    TITULOS_FICHAS: TITULOS_FICHAS,
    resolverRuta: resolverRuta,
    hashDe: hashDe,
    enlaceSeccion: enlaceSeccion,
    enConstruccion: enConstruccion,
    marcadaEnConstruccion: marcadaEnConstruccion,
    pasoDeSeccion: pasoDeSeccion,
    fichasDeSeccion: fichasDeSeccion,
    placeholderPorId: placeholderPorId,
    seleccionadasPara: seleccionadasPara,
    textoPlaceholder: textoPlaceholder,
    filtrarIncidencias: filtrarIncidencias,
    alternarSeleccion: alternarSeleccion,
    buscarPorId: buscarPorId,
    etiquetaEstado: etiquetaEstado,
    formatoImporte: formatoImporte,
    etiquetaCatalogo: etiquetaCatalogo,
  };

  if (typeof window !== "undefined") {
    window.Portal = Portal;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = Portal;
  }
})();
