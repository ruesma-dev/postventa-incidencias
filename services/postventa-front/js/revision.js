// services/postventa-front/js/revision.js
// F-038 R3-R13, R21, R22, R24 · La bandeja de revisión (`bandeja.html`).
//
// `specs/F-038-bandeja-revision/design.md` §2.4 (con su tabla «Conciliado
// 2026-10-20»), contra el contrato **implementado** de F-056, F-059 y F-060
// (`services/postventa-api/interface_adapters/api/revision.py` y
// `domain/models/revision.py`): `GET /api/revision` paginado,
// `GET /api/revision/historial` y `POST /api/revision/acciones`.
//
// - **Lógica pura** (`tests_js/revision.test.js`): los textos de motivos y
//   estados, las acciones de cada estado, la consulta y la paginación, el
//   ajuste del resumen, el formulario (unidad → ubicaciones, oficio →
//   proveedores, lo que está fuera del catálogo de hoy), el cuerpo de cada
//   acción, qué hacer con cada error y la presentación del volcado (R21).
// - **El componente Alpine** `appRevision`, construido por
//   `crearAppRevision({api, parametros})`.
//
// **Nada sale sin un clic (R10).** Cargar solo lee; las acciones salen solo de
// los métodos que el HTML llama desde un `@click`, y el único sitio donde se
// escribe la confirmación es `cuerpoDeAccion`. Mientras una acción se guarda no
// sale otra. La acción no se reintenta sola (`js/api.js`, `sinReintentos`).
//
// **R15.** Ni el correo ni el `oid` van a `console` ni al almacenamiento del
// navegador: aquí no hay ninguna de las dos cosas. La página no normaliza
// ubicaciones (R23): esa ruta no se nombra.
//
// **La presentación del volcado (R21, Q-6).** Del objeto `volcado` de cada
// incidencia (F-059 R4; `volcado_de` del backend) sale UNA línea ya compuesta
// (`lineaDeVolcado`, con la fecha de Madrid y quien volcó por `quienLegible`):
// el HTML no lee el objeto. Una `volcada` o una `en_duda` no admite ninguna
// acción (`accionesDe`) y lleva «Ya no se revisa aquí» junto a su etiqueta.

(function () {
  "use strict";

  /** Los estados de `EstadoRevision`, en su orden (F-056 §3.2, F-059 §4). */
  const ESTADOS = ["nueva", "editada", "aprobada", "descartada", "volcada", "en_duda"];

  const ETIQUETA_ESTADO = {
    nueva: "Nueva",
    editada: "Editada",
    aprobada: "Aprobada",
    descartada: "Descartada",
    volcada: "Volcada a Sigrid",
    en_duda: "En duda",
  };

  /** Los motivos de `MotivoNoAprobable`, en el orden de R21 de F-056. */
  const MOTIVOS = [
    "unidad_fuera_de_la_obra",
    "sin_ubicacion",
    "ubicacion_fuera_de_lista",
    "sin_oficio",
    "oficio_ambiguo",
    "oficio_fuera_de_la_obra",
    "par_fuera_de_la_obra",
    "proveedor_ambiguo",
    "duplicada",
  ];

  /** Los textos de F-056 design §3.5. El de `duplicada` no lleva N: la fila la dice `duplicadaDe`. */
  const TEXTO_MOTIVO = {
    unidad_fuera_de_la_obra: "La unidad ya no es de la obra en Sigrid",
    sin_ubicacion: "Falta la ubicación",
    ubicacion_fuera_de_lista: "La ubicación no está en la lista",
    sin_oficio: "Falta el oficio",
    oficio_ambiguo: "Elige el código del oficio: hay varios en la obra",
    oficio_fuera_de_la_obra: "Este oficio ya no está en la obra en Sigrid",
    par_fuera_de_la_obra: "Este proveedor ya no está en la obra con ese oficio",
    proveedor_ambiguo: "Elige el proveedor",
    duplicada: "Duplicada de otra fila: descarta una o distínguelas",
  };

  /** Lo que admite cada estado: `_PERMITIDAS` (F-056 §3.3, F-059 §4.2). */
  const ACCIONES_POR_ESTADO = {
    nueva: ["editar", "descartar", "aprobar"],
    editada: ["editar", "descartar", "aprobar"],
    aprobada: ["editar", "descartar"],
    descartada: ["recuperar"],
    volcada: [],
    en_duda: [],
  };

  const ACCIONES = ["editar", "descartar", "aprobar", "recuperar"];

  /** Cómo se lee cada acción en el historial. */
  const TEXTO_ACCION = {
    editar: "Editada",
    descartar: "Descartada",
    aprobar: "Aprobada",
    recuperar: "Recuperada",
  };

  /**
   * El selector de estado (R6, R21.5), con `activas` (todo menos descartadas
   * y volcadas) primero, que es el de por defecto.
   */
  const FILTROS_DE_ESTADO = ["activas", "todas", "nueva", "editada", "aprobada", "descartada", "volcada", "en_duda"];

  /** R21.6 · los estados que ya están, o pueden estar, en Sigrid: ninguna acción, y la frase. */
  const ESTADOS_DEL_VOLCADO = ["volcada", "en_duda"];
  const TEXTO_YA_NO_SE_REVISA = "Ya no se revisa aquí";

  /**
   * R21.4 · los códigos de parte de `POST /api/sigrid/partes-reclamacion`
   * (`azure-apps/sigrid_api.md` §8.9), en su orden, con su texto. Son lo que
   * trae el `motivo` del objeto `volcado`; los motivos propios del panel de
   * volcado (exclusiones de un ensayo) no salen ahí y son de F-040.
   */
  const MOTIVOS_DE_VOLCADO = [
    "referencia_no_permitida",
    "referencia_duplicada_en_lote",
    "referencia_en_conflicto",
    "unidad_postventa_no_encontrada",
    "tipo_no_valido",
    "clase_no_valida",
    "oficio_no_esta_en_la_obra",
    "interviniente_no_esta_en_la_obra",
    "interviniente_ambiguo",
    "interviniente_repetido",
    "numeracion_agotada",
    "colision_de_clave",
    "filas_afectadas_inesperadas",
    "error_de_escritura",
    "presupuesto_de_tiempo_agotado",
  ];

  const TEXTO_MOTIVO_VOLCADO = {
    referencia_no_permitida: "Sigrid no admite la referencia del parte",
    referencia_duplicada_en_lote: "La referencia del parte iba repetida en el mismo envío",
    referencia_en_conflicto: "En Sigrid ya hay un parte con esa referencia que no casa (de otra unidad, sin ficha o repetido)",
    unidad_postventa_no_encontrada: "La unidad no está en la obra en Sigrid",
    tipo_no_valido: "El tipo de reclamación no existe en Sigrid",
    clase_no_valida: "La clase de reclamación no existe en Sigrid",
    oficio_no_esta_en_la_obra: "El oficio no está en la obra en Sigrid",
    interviniente_no_esta_en_la_obra: "El oficio y el proveedor no están juntos en la obra en Sigrid",
    interviniente_ambiguo: "El oficio tiene varios proveedores en la obra: hay que elegir uno",
    interviniente_repetido: "El mismo oficio y proveedor iban dos veces en el parte",
    numeracion_agotada: "Se ha agotado la numeración de partes en Sigrid",
    colision_de_clave: "Sigrid estaba creando otro parte a la vez: se puede volver a mandar sin riesgo",
    filas_afectadas_inesperadas: "Sigrid no escribió las filas que se esperaban; el parte no se creó",
    error_de_escritura: "Sigrid dio un error al escribir el parte; no se creó",
    presupuesto_de_tiempo_agotado: "Se acabó el tiempo antes de llegar a este parte: se puede volver a mandar sin riesgo",
  };

  /** Las ocho claves de `valores` de una edición (`CAMPOS_PEDIDOS`). */
  const CAMPOS_PEDIDOS = [
    "unidad_codigo",
    "ubicacion",
    "descripcion",
    "detalle",
    "oficio_codigo",
    "proveedor_codigo",
    "urgencia",
    "listado",
  ];

  /** Los ocho campos lógicos de `cambios` y `campos_cambiados`, con su etiqueta. */
  const CAMPOS_LOGICOS = [
    ["unidad", "Unidad"],
    ["ubicacion", "Ubicación"],
    ["descripcion", "Descripción"],
    ["detalle", "Detalle"],
    ["oficio", "Oficio"],
    ["proveedor", "Proveedor"],
    ["urgencia", "Urgencia"],
    ["listado", "Listado"],
  ];

  const MAX_DESCRIPCION = 128;
  const MAX_DETALLE = 2000;
  const MAX_MOTIVO = 500;
  const LARGO_DESCRIPCION_CORTA = 80;

  const TEXTO_FUERA_DE_LISTA = "no está en la lista de Sigrid de hoy";
  const LITERAL_NORMALIZAR = "sistema:normalizar_ubicacion";
  const TEXTO_NORMALIZAR = "el sistema (ubicación puesta en el texto exacto de Sigrid)";

  const TEXTO_PETICION_INVALIDA =
    "La página ha mandado algo que el servicio no acepta; no se ha guardado nada. Recarga la página.";
  const TEXTO_VALORES_NO_VALIDOS =
    "Hay campos que no valen contra Sigrid hoy: mira el problema junto a cada uno.";
  const TEXTO_SIN_CAMBIOS = "No hay cambios que guardar.";
  const TEXTO_NO_ENCONTRADA = "Esta incidencia ya no está en la bandeja. Se ha vuelto a cargar la lista.";
  const TEXTO_DESACTUALIZADA = "Otra persona la ha cambiado. Se ha vuelto a cargar la lista.";
  const TEXTO_SIN_RESPUESTA = "No se sabe si se ha guardado: recarga para verlo.";
  const TEXTO_NO_GUARDADO = "No se ha guardado nada.";
  const TEXTO_RECARGA_PARA_APROBAR = "Recarga para ver si se puede aprobar.";
  const AVISO_UBICACION = "Esta ubicación no es de la nueva unidad: se ha quitado.";
  const AVISO_PROVEEDOR = "Este proveedor no es del nuevo oficio: se ha quitado.";

  // --- Textos -----------------------------------------------------------------

  function textoMotivo(codigo) {
    return TEXTO_MOTIVO[codigo] || String(codigo);
  }

  function etiquetaEstado(estado) {
    return ETIQUETA_ESTADO[estado] || String(estado);
  }

  /** R11 · una copia: quien la toque no cambia la tabla. Un estado desconocido, nada. */
  function accionesDe(estado) {
    const acciones = Object.prototype.hasOwnProperty.call(ACCIONES_POR_ESTADO, estado)
      ? ACCIONES_POR_ESTADO[estado]
      : [];
    return acciones.slice();
  }

  /** R22 · el correo tal cual; las revisiones del sistema, en castellano. */
  function quienLegible(texto) {
    if (typeof texto !== "string" || !texto) {
      return "";
    }
    if (texto === LITERAL_NORMALIZAR) {
      return TEXTO_NORMALIZAR;
    }
    if (texto.indexOf("sistema:") === 0) {
      return "el sistema";
    }
    return texto;
  }

  // --- La fecha de Madrid -----------------------------------------------------
  //
  // `js/importacion.js` no exporta la suya (y es solo el día): esta va con
  // hora, sin tocar aquel módulo (design.md §2.4).

  const FECHA_HORA_DE_MADRID = new Intl.DateTimeFormat("es-ES", {
    timeZone: "Europe/Madrid",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  });

  /** AAAA-MM-DD hh:mm[:ss[.fracción]] con desfase opcional (el `isoformat` de Python). */
  const FECHA_ISO = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2})(?:\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?$/i;

  /** El instante de una fecha ISO, o `null`. Sin desfase, UTC (los campos son `_utc`). */
  function instanteDeIso(texto) {
    const partes = typeof texto === "string" ? FECHA_ISO.exec(texto.trim()) : null;
    if (!partes) {
      return null;
    }
    const [anio, mes, dia, hora, minuto, segundo] = partes.slice(1, 7).map(function (parte) {
      return Number(parte || 0);
    });
    const enUtc = new Date(Date.UTC(anio, mes - 1, dia, hora, minuto, segundo));
    if (
      enUtc.getUTCFullYear() !== anio || enUtc.getUTCMonth() !== mes - 1 || enUtc.getUTCDate() !== dia ||
      hora > 23 || minuto > 59 || segundo > 59
    ) {
      return null;
    }
    const desfase = partes[7] && partes[7].toUpperCase() !== "Z" ? partes[7] : "";
    if (!desfase) {
      return enUtc;
    }
    const cifras = desfase.slice(1).replace(":", "");
    const horas = Number(cifras.slice(0, 2));
    const minutos = Number(cifras.slice(2));
    if (horas > 23 || minutos > 59) {
      return null;
    }
    const signo = desfase[0] === "-" ? -1 : 1;
    return new Date(enUtc.getTime() - signo * (horas * 60 + minutos) * 60000);
  }

  /** R4, R8 · `dd/mm/aaaa hh:mm` en hora de Madrid; vacío si no es una fecha. */
  function fechaDeMadrid(iso) {
    const instante = instanteDeIso(iso);
    if (!instante) {
      return "";
    }
    const partes = {};
    FECHA_HORA_DE_MADRID.formatToParts(instante).forEach(function (parte) {
      partes[parte.type] = parte.value;
    });
    return partes.day + "/" + partes.month + "/" + partes.year + " " + partes.hour + ":" + partes.minute;
  }

  // --- La fila ----------------------------------------------------------------

  /** «código · nombre», o lo que haya. */
  function conCodigo(nombre, codigo) {
    if (codigo && nombre && nombre !== codigo) {
      return codigo + " · " + nombre;
    }
    return codigo || nombre || "";
  }

  function textoOficio(v) {
    if (v.oficio_ambiguo) {
      const sinElegir = "sin elegir: varios códigos en la obra";
      return v.oficio_nombre ? v.oficio_nombre + " · " + sinElegir : sinElegir;
    }
    return v.oficio_codigo ? conCodigo(v.oficio_nombre, v.oficio_codigo) : "sin oficio";
  }

  function textoProveedor(v) {
    if (v.proveedor_ambiguo) {
      return (v.proveedor_nombre ? v.proveedor_nombre + " · " : "") + "sin elegir";
    }
    return v.proveedor_codigo ? conCodigo(v.proveedor_nombre, v.proveedor_codigo) : "sin proveedor";
  }

  /** La etiqueta de una opción tasada del catálogo (`urgencias`, `listados`), o el código. */
  function etiquetaDe(lista, codigo) {
    const encontrada = (lista || []).find(function (opcion) {
      return opcion && opcion.codigo === codigo;
    });
    return (encontrada && encontrada.etiqueta) || codigo || "";
  }

  /** R4 (b) · `duplicada_de` es un `incidencia_id`: N es su fila, si está cargada. */
  function duplicadaDe(fila, cargadas) {
    if (!fila || !fila.duplicada_de) {
      return null;
    }
    const original = (cargadas || []).find(function (otra) {
      return otra && otra.incidencia_id === fila.duplicada_de;
    });
    if (original && original.fila_origen !== null && original.fila_origen !== undefined) {
      return "duplicada de la fila " + original.fila_origen;
    }
    return "duplicada de otra fila del mismo fichero";
  }

  /**
   * R4, D-8 · «<acción> por <quién> el <fecha>» de la última revisión.
   *
   * La fila no trae la acción de la última revisión, solo el estado: una
   * `aprobada` (y una `volcada` o `en_duda`, cuya última es un `aprobar`) se
   * lee «Aprobada»; una `descartada`, «Descartada»; y una `nueva` o `editada`
   * con revisiones, «Revisada» (puede venir de editar o de recuperar: el
   * historial lo dice).
   */
  function lineaDeRevision(fila) {
    if (!fila || !fila.revisado_at_utc) {
      return null;
    }
    let accion = "Revisada";
    if (fila.estado === "aprobada" || fila.estado === "volcada" || fila.estado === "en_duda") {
      accion = "Aprobada";
    } else if (fila.estado === "descartada") {
      accion = "Descartada";
    }
    return accion + " por " + quienLegible(fila.revisado_por) + " el " + fechaDeMadrid(fila.revisado_at_utc);
  }

  /** R21.4 · el texto de un código de parte de §8.9; uno desconocido, tal cual; sin código, nada. */
  function textoMotivoVolcado(codigo) {
    if (codigo === null || codigo === undefined || codigo === "") {
      return "";
    }
    return Object.prototype.hasOwnProperty.call(TEXTO_MOTIVO_VOLCADO, codigo)
      ? TEXTO_MOTIVO_VOLCADO[codigo]
      : String(codigo);
  }

  /**
   * R21.1-R21.3 · la línea del objeto `volcado` de una incidencia en `estado`,
   * o `null`. Manda el `estado` del objeto:
   *
   * - `volcada`: «Volcada como <sigrid_cod> por <quien> el <fecha>»;
   * - `en_duda`: «Se mandó a Sigrid el <fecha> por <quien> y no consta si se
   *   creó: …» y, si trae motivo, «. Motivo: <texto>»;
   * - `rechazado` o `no_procesado` (el último intento no creó el parte), solo
   *   si la incidencia no está volcada ni en duda: «Último intento de volcado:
   *   no se creó | no se llegó a procesar el <fecha> por <quien>: <texto>».
   *
   * Sin objeto, o con otro estado, nada. La fecha, en hora de Madrid; quien
   * volcó (un correo, D-8), por `quienLegible`, y a ningún otro sitio (R21.7).
   */
  function lineaDeVolcado(volcado, estado) {
    if (!volcado || typeof volcado !== "object") {
      return null;
    }
    const fecha = fechaDeMadrid(volcado.volcado_at_utc);
    const quien = quienLegible(volcado.volcado_por);
    const motivo = textoMotivoVolcado(volcado.motivo);
    switch (volcado.estado) {
      case "volcada":
        return "Volcada como " + comoTexto(volcado.sigrid_cod) + " por " + quien + " el " + fecha;
      case "en_duda":
        return (
          "Se mandó a Sigrid el " + fecha + " por " + quien +
          " y no consta si se creó: volver a ensayar y volcar lo aclara sin duplicar" +
          (motivo ? ". Motivo: " + motivo : "")
        );
      case "rechazado":
      case "no_procesado":
        if (ESTADOS_DEL_VOLCADO.indexOf(estado) !== -1) {
          return null;
        }
        return (
          "Último intento de volcado: " +
          (volcado.estado === "rechazado" ? "no se creó" : "no se llegó a procesar") +
          " el " + fecha + " por " + quien +
          (motivo ? ": " + motivo : "")
        );
      default:
        return null;
    }
  }

  /** R11, R12 · «Aprobar» solo con motivos `[]` y en un estado que lo admite. */
  function puedeAprobar(fila) {
    return (
      Boolean(fila) &&
      Array.isArray(fila.motivos_no_aprobable) &&
      fila.motivos_no_aprobable.length === 0 &&
      accionesDe(fila.estado).indexOf("aprobar") !== -1
    );
  }

  function descripcionCorta(texto) {
    const limpio = String(texto || "");
    if (limpio.length <= LARGO_DESCRIPCION_CORTA) {
      return limpio;
    }
    return limpio.slice(0, LARGO_DESCRIPCION_CORTA).trimEnd() + "…";
  }

  /**
   * R4, R21 · las filas listas para pintar. `respuesta` es `{obra, catalogo,
   * incidencias}`. La línea del volcado va ya compuesta (`lineaVolcado`): en
   * la lista sale con `yaNoSeRevisa` (volcada y en duda) y en el detalle,
   * siempre que la haya (también el último intento fallido, R21.3).
   */
  function presentarRevision(respuesta) {
    const datos = respuesta || {};
    const cargadas = datos.incidencias || [];
    const catalogo = datos.catalogo || {};
    const filas = cargadas.map(function (incidencia) {
      const v = incidencia.vigentes || {};
      const motivos = incidencia.motivos_no_aprobable;
      return {
        incidencia_id: incidencia.incidencia_id,
        fila_origen: incidencia.fila_origen,
        unidad: conCodigo(v.unidad_nombre, v.unidad_codigo),
        ubicacion: v.ubicacion || "",
        descripcion: v.descripcion || "",
        descripcionCorta: descripcionCorta(v.descripcion),
        oficio: textoOficio(v),
        proveedor: textoProveedor(v),
        urgencia: v.urgencia ? etiquetaDe(catalogo.urgencias, v.urgencia) : "",
        listado: v.listado ? etiquetaDe(catalogo.listados, v.listado) : "",
        estado: incidencia.estado,
        etiquetaEstado: etiquetaEstado(incidencia.estado),
        duplicada: duplicadaDe(incidencia, cargadas),
        motivos: Array.isArray(motivos) ? motivos.map(textoMotivo) : [],
        aprobable: puedeAprobar(incidencia),
        avisoAprobar:
          motivos === null && accionesDe(incidencia.estado).indexOf("aprobar") !== -1
            ? TEXTO_RECARGA_PARA_APROBAR
            : "",
        revisadoPor: lineaDeRevision(incidencia),
        yaNoSeRevisa: ESTADOS_DEL_VOLCADO.indexOf(incidencia.estado) !== -1 ? TEXTO_YA_NO_SE_REVISA : "",
        lineaVolcado: lineaDeVolcado(incidencia.volcado, incidencia.estado),
        acciones: accionesDe(incidencia.estado),
        cambios: (incidencia.cambios || []).slice(),
      };
    });
    return { obra: datos.obra, filas: filas };
  }

  /** R5 · el resumen de toda la obra, de la respuesta: seis estados y nueve motivos. */
  function presentarResumen(resumen) {
    if (!resumen) {
      return null;
    }
    const porEstado = resumen.por_estado || {};
    const porMotivo = resumen.por_motivo || {};
    const extras = Object.keys(porMotivo).filter(function (motivo) {
      return MOTIVOS.indexOf(motivo) === -1;
    });
    return {
      total: resumen.total || 0,
      aprobadas: porEstado.aprobada || 0,
      conMotivos: resumen.con_motivos || 0,
      porEstado: ESTADOS.map(function (estado) {
        return { estado: estado, etiqueta: etiquetaEstado(estado), n: porEstado[estado] || 0 };
      }),
      porMotivo: MOTIVOS.concat(extras).map(function (motivo) {
        return { motivo: motivo, texto: textoMotivo(motivo), n: porMotivo[motivo] || 0 };
      }),
    };
  }

  /** El texto de un campo lógico, con los valores de una foto. */
  function textoDeCampo(campo, v, catalogo) {
    const cat = catalogo || {};
    switch (campo) {
      case "unidad":
        return conCodigo(v.unidad_nombre, v.unidad_codigo);
      case "ubicacion":
        return v.ubicacion || "sin ubicación";
      case "descripcion":
        return v.descripcion || "";
      case "detalle":
        return v.detalle || "sin detalle";
      case "oficio":
        return textoOficio(v);
      case "proveedor":
        return textoProveedor(v);
      case "urgencia":
        return v.urgencia ? etiquetaDe(cat.urgencias, v.urgencia) : "sin urgencia";
      case "listado":
        return v.listado ? etiquetaDe(cat.listados, v.listado) : "sin listado";
      default:
        return "";
    }
  }

  function etiquetaDeCampo(campo) {
    const encontrado = CAMPOS_LOGICOS.find(function (par) {
      return par[0] === campo;
    });
    return encontrado ? encontrado[1] : String(campo);
  }

  /** R8 · los vigentes y, en cada campo de `cambios`, «llegó así: …». */
  function detalleDe(incidencia, catalogo) {
    const fila = incidencia || {};
    const vigentes = fila.vigentes || {};
    const importados = fila.importados || {};
    const cambios = fila.cambios || [];
    return CAMPOS_LOGICOS.map(function (par) {
      const campo = par[0];
      return {
        campo: campo,
        etiqueta: par[1],
        valor: textoDeCampo(campo, vigentes, catalogo),
        llegoAsi:
          cambios.indexOf(campo) !== -1 ? "llegó así: " + textoDeCampo(campo, importados, catalogo) : null,
      };
    });
  }

  /** R8, R22 · el historial, con fecha de Madrid y quién legible. */
  function presentarHistorial(respuesta) {
    const datos = respuesta || {};
    const importada = datos.importada || {};
    return {
      incidencia_id: datos.incidencia_id || null,
      importada: fechaDeMadrid(importada.creada_at_utc),
      revisiones: (datos.revisiones || []).map(function (revision) {
        return {
          revision_id: revision.revision_id,
          fecha: fechaDeMadrid(revision.revisado_at_utc),
          accion: TEXTO_ACCION[revision.accion] || String(revision.accion),
          quien: quienLegible(revision.correo),
          campos: (revision.campos_cambiados || []).map(etiquetaDeCampo),
          motivo: revision.motivo || "",
        };
      }),
    };
  }

  // --- La consulta y la paginación (R3, R6, R7) -----------------------------------

  /**
   * Los parámetros de `GET /api/revision`, solo los que tocan: la obra, el
   * estado (de los del selector; si no, `activas`), `con_motivos` solo si se
   * pide y el cursor tal cual. **Nunca `tamano`** (R7).
   */
  function consultaDe(obra, filtros, cursor) {
    const elegidos = filtros || {};
    const estado =
      FILTROS_DE_ESTADO.indexOf(elegidos.estado) !== -1 ? elegidos.estado : FILTROS_DE_ESTADO[0];
    const consulta = { obra: String(obra || "").trim(), estado: estado };
    if (elegidos.conMotivos === true) {
      consulta.con_motivos = true;
    }
    if (typeof cursor === "string" && cursor) {
      consulta.cursor = cursor;
    }
    return consulta;
  }

  /** R7 · añade una página sin repetir por `incidencia_id`, con su `siguiente` y «N de M». */
  function anadirPagina(cargadas, respuesta) {
    const datos = respuesta || {};
    const vistos = new Set();
    const incidencias = [];
    (cargadas || []).concat(datos.incidencias || []).forEach(function (incidencia) {
      if (incidencia && !vistos.has(incidencia.incidencia_id)) {
        vistos.add(incidencia.incidencia_id);
        incidencias.push(incidencia);
      }
    });
    const total = typeof datos.total_filtrado === "number" ? datos.total_filtrado : incidencias.length;
    return {
      incidencias: incidencias,
      siguiente: typeof datos.siguiente === "string" && datos.siguiente ? datos.siguiente : null,
      cargadas: incidencias.length,
      total: total,
      nDeM: incidencias.length + " de " + total,
    };
  }

  /**
   * R12 · el resumen tras una acción, con la diferencia entre la fila de antes
   * y la de después. Los motivos solo se mueven si las dos los traen: con
   * `motivos_no_aprobable: null` (descartar, recuperar: los valores no
   * cambian) solo se mueve el estado. Lo que no se puede ajustar aquí (el
   * `duplicada` de otra fila) se corrige al pedir otra vez la primera página.
   */
  function ajustarResumen(resumen, antes, despues) {
    if (!resumen) {
      return resumen;
    }
    const nuevo = {
      total: resumen.total,
      por_estado: Object.assign({}, resumen.por_estado),
      con_motivos: resumen.con_motivos,
      por_motivo: Object.assign({}, resumen.por_motivo),
    };
    const de = (antes && antes.estado) || null;
    const a = (despues && despues.estado) || null;
    if (de) {
      nuevo.por_estado[de] = (nuevo.por_estado[de] || 0) - 1;
    }
    if (a) {
      nuevo.por_estado[a] = (nuevo.por_estado[a] || 0) + 1;
    }
    const motivosAntes = antes && antes.motivos_no_aprobable;
    const motivosDespues = despues && despues.motivos_no_aprobable;
    if (Array.isArray(motivosAntes) && Array.isArray(motivosDespues)) {
      motivosAntes.forEach(function (motivo) {
        nuevo.por_motivo[motivo] = (nuevo.por_motivo[motivo] || 0) - 1;
      });
      motivosDespues.forEach(function (motivo) {
        nuevo.por_motivo[motivo] = (nuevo.por_motivo[motivo] || 0) + 1;
      });
      nuevo.con_motivos =
        (nuevo.con_motivos || 0) - (motivosAntes.length ? 1 : 0) + (motivosDespues.length ? 1 : 0);
    }
    return nuevo;
  }

  // --- El formulario (R9, R24) -------------------------------------------------------

  function marcado(texto) {
    return texto + " (" + TEXTO_FUERA_DE_LISTA + ")";
  }

  function estaEn(lista, codigo) {
    return (lista || []).some(function (opcion) {
      return opcion && opcion.codigo === codigo;
    });
  }

  /** Las ubicaciones de la tipología de la unidad (`catalogo.ubicaciones[unidad]`). */
  function ubicacionesDe(catalogo, unidadCodigo) {
    const porUnidad = (catalogo && catalogo.ubicaciones) || {};
    const lista = Object.prototype.hasOwnProperty.call(porUnidad, unidadCodigo) ? porUnidad[unidadCodigo] : null;
    return Array.isArray(lista) ? lista.slice() : [];
  }

  /** Los pares de un oficio, cada uno como opción. */
  function paresDe(catalogo, oficio) {
    return ((catalogo && catalogo.pares) || [])
      .filter(function (par) {
        return par && par.oficio_codigo === oficio && par.proveedor_codigo;
      })
      .map(function (par) {
        return {
          codigo: par.proveedor_codigo,
          texto: conCodigo(par.proveedor_nombre, par.proveedor_codigo),
          fueraDeLista: false,
        };
      });
  }

  /** R24 · las unidades de la obra y, si la vigente ya no lo es, ella marcada. */
  function opcionesDeUnidad(catalogo, vigentes) {
    const opciones = ((catalogo && catalogo.unidades) || []).map(function (unidad) {
      return { codigo: unidad.codigo, texto: conCodigo(unidad.nombre, unidad.codigo), fueraDeLista: false };
    });
    const v = vigentes || {};
    if (v.unidad_codigo && !estaEn(opciones, v.unidad_codigo)) {
      opciones.push({
        codigo: v.unidad_codigo,
        texto: marcado(conCodigo(v.unidad_nombre, v.unidad_codigo)),
        fueraDeLista: true,
      });
    }
    return opciones;
  }

  /** R9, R24 · las ubicaciones de la unidad elegida y, en la vigente, la conservada marcada. */
  function opcionesDeUbicacion(catalogo, unidadCodigo, vigentes) {
    const lista = ubicacionesDe(catalogo, unidadCodigo);
    const opciones = lista.map(function (ubicacion) {
      return { codigo: ubicacion, texto: ubicacion, fueraDeLista: false };
    });
    const v = vigentes || {};
    if (unidadCodigo === v.unidad_codigo && v.ubicacion && lista.indexOf(v.ubicacion) === -1) {
      opciones.push({ codigo: v.ubicacion, texto: marcado(v.ubicacion), fueraDeLista: true });
    }
    return opciones;
  }

  /**
   * R9 (b), R24 · los oficios de la obra por código. Con el oficio vigente
   * ambiguo, los de su grupo (`grupo.etiqueta` igual al `oficio_nombre`)
   * primero; un oficio vigente que ya no está, conservado y marcado.
   */
  function opcionesDeOficio(catalogo, vigentes) {
    const v = vigentes || {};
    const opciones = ((catalogo && catalogo.oficios) || []).map(function (oficio) {
      return {
        codigo: oficio.codigo,
        texto: conCodigo(oficio.nombre, oficio.codigo),
        delGrupo: Boolean(v.oficio_ambiguo) && Boolean(oficio.grupo) && oficio.grupo.etiqueta === v.oficio_nombre,
        fueraDeLista: false,
      };
    });
    const ordenadas = opciones
      .filter(function (o) {
        return o.delGrupo;
      })
      .concat(
        opciones.filter(function (o) {
          return !o.delGrupo;
        }),
      );
    if (v.oficio_codigo && !v.oficio_ambiguo && !estaEn(ordenadas, v.oficio_codigo)) {
      ordenadas.push({
        codigo: v.oficio_codigo,
        texto: marcado(conCodigo(v.oficio_nombre, v.oficio_codigo)),
        delGrupo: false,
        fueraDeLista: true,
      });
    }
    return ordenadas;
  }

  /**
   * R9 (a), (c), R24 · los proveedores del oficio elegido, de `catalogo.pares`.
   * Sin oficio elegido: si el vigente es ambiguo, solo su proveedor vigente
   * (F-056 R15); si no, ninguno (no hay proveedor sin oficio). Con el oficio
   * vigente, un proveedor vigente cuyo par ya no está, conservado y marcado.
   */
  function proveedoresDe(catalogo, oficio, vigentes) {
    const v = vigentes || {};
    if (!oficio) {
      if (v.oficio_ambiguo && v.proveedor_codigo) {
        return [{ codigo: v.proveedor_codigo, texto: conCodigo(v.proveedor_nombre, v.proveedor_codigo), fueraDeLista: false }];
      }
      return [];
    }
    const opciones = paresDe(catalogo, oficio);
    if (oficio === v.oficio_codigo && v.proveedor_codigo && !estaEn(opciones, v.proveedor_codigo)) {
      opciones.push({
        codigo: v.proveedor_codigo,
        texto: marcado(conCodigo(v.proveedor_nombre, v.proveedor_codigo)),
        fueraDeLista: true,
      });
    }
    return opciones;
  }

  function comoTexto(valor) {
    return valor === null || valor === undefined ? "" : String(valor);
  }

  /**
   * R9, R24 · el formulario de unos vigentes: textos (vacío = «»), el aviso,
   * los vigentes (para las opciones y para `hayCambios`) y qué valor vigente
   * no está en el catálogo de hoy. Nada se vacía en silencio al abrir.
   */
  function formularioDe(vigentes, catalogo) {
    const v = vigentes || {};
    const cat = catalogo || {};
    const unidadFuera = Boolean(v.unidad_codigo) && !estaEn(cat.unidades, v.unidad_codigo);
    const ubicacionFuera =
      Boolean(v.ubicacion) && ubicacionesDe(cat, v.unidad_codigo).indexOf(v.ubicacion) === -1;
    const oficioFuera = Boolean(v.oficio_codigo) && !v.oficio_ambiguo && !estaEn(cat.oficios, v.oficio_codigo);
    const proveedorFuera =
      Boolean(v.proveedor_codigo) &&
      !v.oficio_ambiguo &&
      !v.proveedor_ambiguo &&
      !estaEn(paresDe(cat, v.oficio_codigo), v.proveedor_codigo);
    return {
      unidad_codigo: comoTexto(v.unidad_codigo),
      ubicacion: comoTexto(v.ubicacion),
      descripcion: comoTexto(v.descripcion),
      detalle: comoTexto(v.detalle),
      oficio_codigo: comoTexto(v.oficio_codigo),
      proveedor_codigo: comoTexto(v.proveedor_codigo),
      urgencia: comoTexto(v.urgencia),
      listado: comoTexto(v.listado),
      aviso: "",
      vigentes: Object.assign({}, v),
      fueraDeLista: {
        unidad: unidadFuera,
        ubicacion: ubicacionFuera,
        oficio: oficioFuera,
        proveedor: proveedorFuera,
      },
    };
  }

  /** R9 · al cambiar la unidad, la ubicación se revalida contra la nueva (comparación exacta). */
  function alCambiarUnidad(formulario, catalogo) {
    const nuevo = Object.assign({}, formulario, { aviso: "" });
    if (nuevo.ubicacion && ubicacionesDe(catalogo, nuevo.unidad_codigo).indexOf(nuevo.ubicacion) === -1) {
      nuevo.ubicacion = "";
      nuevo.aviso = AVISO_UBICACION;
    }
    return nuevo;
  }

  /** R9 · al cambiar el oficio, el proveedor que no casa se vacía. */
  function alCambiarOficio(formulario, catalogo) {
    const nuevo = Object.assign({}, formulario, { aviso: "" });
    const opciones = proveedoresDe(catalogo, nuevo.oficio_codigo, nuevo.vigentes);
    if (nuevo.proveedor_codigo && !estaEn(opciones, nuevo.proveedor_codigo)) {
      nuevo.proveedor_codigo = "";
      nuevo.aviso = AVISO_PROVEEDOR;
    }
    return nuevo;
  }

  function vacioANull(valor) {
    const texto = comoTexto(valor);
    return texto === "" ? null : texto;
  }

  function recortadoONull(valor) {
    const texto = comoTexto(valor).trim();
    return texto === "" ? null : texto;
  }

  /**
   * R9 (c), (d) · las ocho claves de `valores`. Ubicación y detalle, recortados
   * y vacíos → `null` (nunca `""`: es 400 en `ubicacion`); un código vacío,
   * `null` (el oficio ambiguo sin elegir viaja así, F-056 R15).
   */
  function valoresDelFormulario(formulario) {
    const f = formulario || {};
    return {
      unidad_codigo: vacioANull(f.unidad_codigo),
      ubicacion: recortadoONull(f.ubicacion),
      descripcion: comoTexto(f.descripcion),
      detalle: recortadoONull(f.detalle),
      oficio_codigo: vacioANull(f.oficio_codigo),
      proveedor_codigo: vacioANull(f.proveedor_codigo),
      urgencia: vacioANull(f.urgencia),
      listado: vacioANull(f.listado),
    };
  }

  /** La descripción como la deja el backend: los blancos colapsados. */
  function colapsar(texto) {
    return comoTexto(texto).split(/\s+/).filter(Boolean).join(" ");
  }

  function normalizado(valor) {
    return valor === undefined ? null : valor;
  }

  /** R9 (e) · ¿hay algo que guardar? Con la normalización del backend (F-056 R16). */
  function hayCambios(formulario, vigentes) {
    const pedidos = valoresDelFormulario(formulario);
    const v = vigentes || {};
    return (
      pedidos.unidad_codigo !== normalizado(v.unidad_codigo) ||
      pedidos.ubicacion !== recortadoONull(v.ubicacion) ||
      colapsar(pedidos.descripcion) !== colapsar(v.descripcion) ||
      pedidos.detalle !== recortadoONull(v.detalle) ||
      pedidos.oficio_codigo !== normalizado(v.oficio_codigo) ||
      pedidos.proveedor_codigo !== normalizado(v.proveedor_codigo) ||
      pedidos.urgencia !== normalizado(v.urgencia) ||
      pedidos.listado !== normalizado(v.listado)
    );
  }

  function contador(texto, maximo) {
    return comoTexto(texto).length + " / " + maximo;
  }

  // --- El cuerpo de una acción (R10) -----------------------------------------------------

  /**
   * El cuerpo de `POST /api/revision/acciones`: **exactamente** las seis
   * claves comunes, más `valores` (sus ocho claves) en editar y `motivo`
   * (recortado, si lo hay) en descartar. La `revision_id` de la fila va como
   * `revision_previa`. Es el ÚNICO sitio que confirma una acción.
   */
  function cuerpoDeAccion(fila, accion, extra, identidad) {
    if (ACCIONES.indexOf(accion) === -1) {
      throw new Error("una acción es editar, descartar, aprobar o recuperar");
    }
    if (!identidad || !identidad.usuarioOid || !identidad.correo) {
      throw new Error("sin oid o sin correo no se manda ninguna acción");
    }
    const datos = extra || {};
    const cuerpo = {
      incidencia_id: fila.incidencia_id,
      accion: accion,
      usuario_oid: identidad.usuarioOid,
      usuario_correo: identidad.correo,
      confirmado: true,
      revision_previa: fila.revision_id === undefined ? null : fila.revision_id,
    };
    if (accion === "editar") {
      if (!datos.valores || typeof datos.valores !== "object") {
        throw new Error("editar necesita los valores del formulario");
      }
      const valores = {};
      CAMPOS_PEDIDOS.forEach(function (campo) {
        valores[campo] = datos.valores[campo] === undefined ? null : datos.valores[campo];
      });
      cuerpo.valores = valores;
    }
    if (accion === "descartar") {
      const motivo = typeof datos.motivo === "string" ? datos.motivo.trim() : "";
      if (motivo.length > MAX_MOTIVO) {
        throw new Error("el motivo pasa de " + MAX_MOTIVO + " caracteres");
      }
      if (motivo) {
        cuerpo.motivo = motivo;
      }
    }
    return cuerpo;
  }

  /** R10 · sin `oid`, sin correo o guardando, ningún botón de acción. */
  function puedeActuar(identidad, guardando) {
    return Boolean(identidad && identidad.usuarioOid && identidad.correo) && !guardando;
  }

  // --- Qué hacer con un error (R12, R26) ---------------------------------------------------

  function textoDelServicio(error) {
    return error.mensajeServicio || error.mensaje || error.message || "Error desconocido.";
  }

  function minusculaInicial(texto) {
    return texto ? texto.charAt(0).toLowerCase() + texto.slice(1) : texto;
  }

  /**
   * La tabla de R12: `{mensaje, recargar, erroresPorCampo, motivos}`. Lee
   * `error.codigo`, `error.http` y `error.detalle` (R26). `enAccion` dice si
   * venía de una acción: sin respuesta, una acción «no se sabe si se ha
   * guardado» y se recarga; una lectura solo dice su error.
   */
  function queHacerConElError(error, enAccion) {
    const salida = { mensaje: "", recargar: false, erroresPorCampo: null, motivos: null };
    if (!error) {
      salida.mensaje = "Error desconocido.";
      return salida;
    }
    const detalle = (error.detalle && typeof error.detalle === "object" && error.detalle) || {};
    if (error.http === null || error.http === undefined) {
      if (enAccion) {
        salida.mensaje = TEXTO_SIN_RESPUESTA;
        salida.recargar = true;
      } else {
        salida.mensaje = error.mensaje || error.message || "Error desconocido.";
      }
      return salida;
    }
    switch (error.codigo) {
      case "peticion_invalida":
        salida.mensaje = TEXTO_PETICION_INVALIDA;
        return salida;
      case "valores_no_validos": {
        const porCampo = {};
        (Array.isArray(detalle.errores) ? detalle.errores : []).forEach(function (cada) {
          if (cada && typeof cada.campo === "string") {
            porCampo[cada.campo] = String(cada.problema || "");
          }
        });
        salida.mensaje = TEXTO_VALORES_NO_VALIDOS;
        salida.erroresPorCampo = porCampo;
        return salida;
      }
      case "sin_cambios":
        salida.mensaje = TEXTO_SIN_CAMBIOS;
        return salida;
      case "incidencia_no_encontrada":
        salida.mensaje = TEXTO_NO_ENCONTRADA;
        salida.recargar = true;
        return salida;
      case "accion_no_permitida":
        salida.mensaje =
          "Esta incidencia está " + minusculaInicial(etiquetaEstado(detalle.estado)) + ": ya no admite esa acción.";
        salida.recargar = true;
        return salida;
      case "revision_desactualizada":
        salida.mensaje = TEXTO_DESACTUALIZADA;
        salida.recargar = true;
        return salida;
      case "incidencia_no_aprobable":
        salida.motivos = (Array.isArray(detalle.motivos) ? detalle.motivos : []).map(textoMotivo);
        salida.mensaje = "No se puede aprobar: " + salida.motivos.join("; ") + ".";
        return salida;
      case "bandeja_demasiado_grande":
        salida.mensaje =
          "La obra pasa del tope de la bandeja" +
          (typeof detalle.total === "number" ? " (" + detalle.total + " incidencias)" : "") +
          ": no se puede revisar aquí.";
        return salida;
      default:
        break;
    }
    // `obra_sin_unidades`, `obra_ambigua`, `catalogo_sin_verificar`, el 500 y
    // el 503 (sin `codigo`) y cualquier código que no esté en la tabla: por su
    // HTTP, con el texto del servicio.
    salida.mensaje = textoDelServicio(error);
    if (error.http === 500 && enAccion) {
      salida.mensaje += " " + TEXTO_NO_GUARDADO;
    }
    return salida;
  }

  /** R13 · el `beforeunload`: solo con un formulario con cambios. Ilegible, no pregunta. */
  function hayEdicionSinGuardar(estado) {
    try {
      const formulario = estado && estado.formulario;
      if (!formulario || !formulario.vigentes) {
        return false;
      }
      return hayCambios(formulario, formulario.vigentes);
    } catch (error) {
      return false;
    }
  }

  /** R3 · la obra de `?obra=` (recortada), o vacío. */
  function obraDeLaUrl(busqueda) {
    try {
      const obra = new URLSearchParams(typeof busqueda === "string" ? busqueda : "").get("obra");
      return obra ? obra.trim() : "";
    } catch (error) {
      return "";
    }
  }

  // --- El componente Alpine -------------------------------------------------------------------

  /**
   * El estado de `bandeja.html`. `dependencias.api` es el cliente de
   * `js/api.js` (o un doble); `dependencias.parametros`, la cadena de consulta
   * de la URL (`?obra=`). Solo guarda estado y delega en lo puro.
   *
   * Abrir el detalle y el formulario son métodos que reciben un
   * `incidencia_id` (design.md §2.4): F-057 los llamará desde un enlace profundo.
   */
  function crearAppRevision(dependencias) {
    const api = dependencias.api;
    const parametros = dependencias.parametros || "";

    return {
      usuario: { usuarioOid: "", correo: "" },
      obra: "",
      filtros: { estado: FILTROS_DE_ESTADO[0], conMotivos: false },
      FILTROS_DE_ESTADO: FILTROS_DE_ESTADO.slice(),
      cargando: false,
      cargandoMas: false,
      errorCarga: "",
      consulta: null,
      obraCargada: "",
      catalogo: null,
      resumen: null,
      incidencias: [],
      siguiente: null,
      nDeM: "",
      abierta: null,
      historial: null,
      errorHistorial: "",
      formulario: null,
      guardando: false,
      mensajeAccion: "",
      erroresPorCampo: null,
      confirmandoDescarte: null,
      motivoDescarte: "",

      async iniciar() {
        this.usuario = await api.identidad();
        const obra = obraDeLaUrl(parametros);
        if (obra) {
          this.obra = obra;
          await this.cargar();
        }
      },

      /** R3, R6 · la primera página con los filtros elegidos. Solo lee. */
      async cargar() {
        const consulta = consultaDe(this.obra, this.filtros, null);
        if (!consulta.obra) {
          return;
        }
        this.cargando = true;
        this.errorCarga = "";
        this.cerrarDetalle();
        try {
          const respuesta = await api.revision(
            consulta.obra,
            { estado: consulta.estado, con_motivos: consulta.con_motivos },
            consulta.cursor,
          );
          const pagina = anadirPagina([], respuesta);
          this.consulta = consulta;
          this.obraCargada = respuesta.obra || consulta.obra;
          this.catalogo = respuesta.catalogo || null;
          this.resumen = respuesta.resumen || null;
          this.incidencias = pagina.incidencias;
          this.siguiente = pagina.siguiente;
          this.nDeM = pagina.nDeM;
        } catch (error) {
          this.consulta = null;
          this.catalogo = null;
          this.resumen = null;
          this.incidencias = [];
          this.siguiente = null;
          this.nDeM = "";
          this.errorCarga = queHacerConElError(error, false).mensaje;
        } finally {
          this.cargando = false;
        }
      },

      /** R6 · cambiar un filtro vuelve a la primera página. */
      async cambiarFiltro() {
        await this.cargar();
      },

      /** R7 · la página siguiente, con el cursor y los mismos filtros de la primera. */
      async cargarMas() {
        if (!this.siguiente || !this.consulta || this.cargandoMas) {
          return;
        }
        const consulta = consultaDe(
          this.consulta.obra,
          { estado: this.consulta.estado, conMotivos: this.consulta.con_motivos === true },
          this.siguiente,
        );
        this.cargandoMas = true;
        this.errorCarga = "";
        try {
          const respuesta = await api.revision(
            consulta.obra,
            { estado: consulta.estado, con_motivos: consulta.con_motivos },
            consulta.cursor,
          );
          const pagina = anadirPagina(this.incidencias, respuesta);
          this.incidencias = pagina.incidencias;
          this.siguiente = pagina.siguiente;
          this.nDeM = pagina.nDeM;
          this.resumen = respuesta.resumen || this.resumen;
          this.catalogo = respuesta.catalogo || this.catalogo;
        } catch (error) {
          this.errorCarga = queHacerConElError(error, false).mensaje;
        } finally {
          this.cargandoMas = false;
        }
      },

      vista() {
        return presentarRevision({ obra: this.obraCargada, catalogo: this.catalogo, incidencias: this.incidencias });
      },

      vistaResumen() {
        return presentarResumen(this.resumen);
      },

      filaDe(incidenciaId) {
        return (
          this.incidencias.find(function (incidencia) {
            return incidencia.incidencia_id === incidenciaId;
          }) || null
        );
      },

      /** R8 · abre el detalle de una incidencia y pide su historial (solo lee). */
      async abrirDetalle(incidenciaId) {
        if (!this.filaDe(incidenciaId)) {
          return;
        }
        if (this.abierta !== incidenciaId) {
          this.formulario = null;
          this.confirmandoDescarte = null;
          this.erroresPorCampo = null;
        }
        this.abierta = incidenciaId;
        this.historial = null;
        this.errorHistorial = "";
        try {
          this.historial = presentarHistorial(await api.historialRevision(incidenciaId));
        } catch (error) {
          this.errorHistorial = queHacerConElError(error, false).mensaje;
        }
      },

      cerrarDetalle() {
        this.abierta = null;
        this.historial = null;
        this.errorHistorial = "";
        this.formulario = null;
        this.confirmandoDescarte = null;
        this.erroresPorCampo = null;
      },

      detalle() {
        const fila = this.filaDe(this.abierta);
        return fila ? detalleDe(fila, this.catalogo) : [];
      },

      /** R9, R11 · abre el formulario de una incidencia, si su estado admite editar. */
      async abrirFormulario(incidenciaId) {
        const fila = this.filaDe(incidenciaId);
        if (!fila || accionesDe(fila.estado).indexOf("editar") === -1) {
          return;
        }
        if (this.abierta !== incidenciaId) {
          await this.abrirDetalle(incidenciaId);
        }
        this.formulario = formularioDe(fila.vigentes, this.catalogo);
        this.erroresPorCampo = null;
        this.mensajeAccion = "";
      },

      cancelarFormulario() {
        this.formulario = null;
        this.erroresPorCampo = null;
      },

      cambiarUnidad() {
        if (this.formulario) {
          this.formulario = alCambiarUnidad(this.formulario, this.catalogo);
        }
      },

      cambiarOficio() {
        if (this.formulario) {
          this.formulario = alCambiarOficio(this.formulario, this.catalogo);
        }
      },

      opciones() {
        const f = this.formulario;
        if (!f) {
          return null;
        }
        const catalogo = this.catalogo || {};
        return {
          unidades: opcionesDeUnidad(catalogo, f.vigentes),
          ubicaciones: opcionesDeUbicacion(catalogo, f.unidad_codigo, f.vigentes),
          oficios: opcionesDeOficio(catalogo, f.vigentes),
          proveedores: proveedoresDe(catalogo, f.oficio_codigo, f.vigentes),
          urgencias: catalogo.urgencias || [],
          listados: catalogo.listados || [],
        };
      },

      puedeActuar() {
        return puedeActuar(this.usuario, this.guardando);
      },

      hayEdicionSinGuardar() {
        return hayEdicionSinGuardar(this);
      },

      /** R9, R10 · «Guardar cambios». Sin cambios no sale nada. */
      async guardarEdicion() {
        if (!this.formulario || !this.abierta) {
          return;
        }
        if (!hayCambios(this.formulario, this.formulario.vigentes)) {
          this.mensajeAccion = TEXTO_SIN_CAMBIOS;
          return;
        }
        await this.actuar(this.abierta, "editar", { valores: valoresDelFormulario(this.formulario) });
      },

      async aprobar(incidenciaId) {
        await this.actuar(incidenciaId, "aprobar", {});
      },

      async recuperar(incidenciaId) {
        await this.actuar(incidenciaId, "recuperar", {});
      },

      /** R11 · el primer clic de «Descartar» solo pide la confirmación en el panel. */
      pedirDescarte(incidenciaId) {
        const fila = this.filaDe(incidenciaId);
        if (!fila || accionesDe(fila.estado).indexOf("descartar") === -1) {
          return;
        }
        this.confirmandoDescarte = incidenciaId;
        this.motivoDescarte = "";
      },

      cancelarDescarte() {
        this.confirmandoDescarte = null;
        this.motivoDescarte = "";
      },

      /** R11 · el segundo clic, sobre la misma fila. */
      async confirmarDescarte(incidenciaId) {
        if (this.confirmandoDescarte !== incidenciaId) {
          return;
        }
        await this.actuar(incidenciaId, "descartar", { motivo: this.motivoDescarte });
      },

      /** R10, R12 · la ÚNICA salida hacia `POST /api/revision/acciones`. */
      async actuar(incidenciaId, accion, extra) {
        if (!puedeActuar(this.usuario, this.guardando)) {
          return;
        }
        const antes = this.filaDe(incidenciaId);
        if (!antes || accionesDe(antes.estado).indexOf(accion) === -1) {
          return;
        }
        const cuerpo = cuerpoDeAccion(antes, accion, extra, this.usuario);
        this.guardando = true;
        this.mensajeAccion = "";
        this.erroresPorCampo = null;
        let recargar = false;
        try {
          const despues = await api.accionRevision(cuerpo);
          // La fila se sustituye en su sitio aunque ya no cumpla el filtro
          // (design.md §2.3): el filtro se aplica al pedir otra vez la lista.
          this.incidencias = this.incidencias.map(function (incidencia) {
            return incidencia.incidencia_id === incidenciaId ? despues : incidencia;
          });
          this.resumen = ajustarResumen(this.resumen, antes, despues);
          this.formulario = null;
          this.confirmandoDescarte = null;
          this.motivoDescarte = "";
        } catch (error) {
          const que = queHacerConElError(error, true);
          this.mensajeAccion = que.mensaje;
          this.erroresPorCampo = que.erroresPorCampo;
          recargar = que.recargar;
        } finally {
          this.guardando = false;
        }
        if (recargar) {
          const mensaje = this.mensajeAccion;
          await this.cargar();
          this.mensajeAccion = mensaje;
        }
      },
    };
  }

  /** El `x-data` de `bandeja.html`: el componente con el `api` de verdad. */
  function appRevision() {
    const config = window.CONFIG_POSTVENTA;
    const api = window.Api.crearApi({ baseApi: config.baseApi, config: config });
    return crearAppRevision({ api: api, parametros: window.location.search });
  }

  const Revision = {
    ESTADOS: ESTADOS,
    MOTIVOS: MOTIVOS,
    TEXTO_MOTIVO: TEXTO_MOTIVO,
    MOTIVOS_DE_VOLCADO: MOTIVOS_DE_VOLCADO,
    FILTROS_DE_ESTADO: FILTROS_DE_ESTADO,
    CAMPOS_PEDIDOS: CAMPOS_PEDIDOS,
    MAX_DESCRIPCION: MAX_DESCRIPCION,
    MAX_DETALLE: MAX_DETALLE,
    MAX_MOTIVO: MAX_MOTIVO,
    textoMotivo: textoMotivo,
    etiquetaEstado: etiquetaEstado,
    accionesDe: accionesDe,
    quienLegible: quienLegible,
    fechaDeMadrid: fechaDeMadrid,
    duplicadaDe: duplicadaDe,
    lineaDeRevision: lineaDeRevision,
    textoMotivoVolcado: textoMotivoVolcado,
    lineaDeVolcado: lineaDeVolcado,
    puedeAprobar: puedeAprobar,
    presentarRevision: presentarRevision,
    presentarResumen: presentarResumen,
    detalleDe: detalleDe,
    presentarHistorial: presentarHistorial,
    consultaDe: consultaDe,
    anadirPagina: anadirPagina,
    ajustarResumen: ajustarResumen,
    ubicacionesDe: ubicacionesDe,
    opcionesDeUnidad: opcionesDeUnidad,
    opcionesDeUbicacion: opcionesDeUbicacion,
    opcionesDeOficio: opcionesDeOficio,
    proveedoresDe: proveedoresDe,
    formularioDe: formularioDe,
    alCambiarUnidad: alCambiarUnidad,
    alCambiarOficio: alCambiarOficio,
    valoresDelFormulario: valoresDelFormulario,
    hayCambios: hayCambios,
    contador: contador,
    cuerpoDeAccion: cuerpoDeAccion,
    puedeActuar: puedeActuar,
    queHacerConElError: queHacerConElError,
    hayEdicionSinGuardar: hayEdicionSinGuardar,
    obraDeLaUrl: obraDeLaUrl,
    crearAppRevision: crearAppRevision,
  };

  if (typeof window !== "undefined") {
    window.Revision = Revision;
    window.appRevision = appRevision;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = Revision;
  }
})();
